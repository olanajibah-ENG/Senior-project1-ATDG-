// Code parser utility to extract class diagrams from Python and Java code

export interface ParsedClass {
  name: string;
  attributes: string[];
  methods: string[];
  isAbstract?: boolean;
  extends?: string;
  implements?: string[];
  visibility?: 'public' | 'private' | 'protected' | 'package';
}

export interface ClassRelationship {
  from: string;
  to: string;
  type: 'inheritance' | 'implementation' | 'composition' | 'aggregation' | 'association' | 'dependency';
  label?: string;
}

export interface DiagramData {
  title: string;
  description: string;
  classes: ParsedClass[];
  relationships: ClassRelationship[];
}

/**
 * Parse Python code and extract class information
 */
function parsePythonCode(code: string): ParsedClass[] {
  const classes: ParsedClass[] = [];
  const lines = code.split('\n');

  let currentClass: ParsedClass | null = null;
  let indentLevel = 0;
  let inMethod = false;
  let methodIndentLevel = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const originalLine = lines[i];

    // Skip empty lines and comments
    if (!line || line.startsWith('#')) continue;

    // Check for class definition with inheritance
    const classMatch = line.match(/^class\s+(\w+)(?:\(([^)]*)\))?:/);
    if (classMatch) {
      // Save previous class if exists
      if (currentClass) {
        classes.push(currentClass);
      }

      // Start new class
      const className = classMatch[1];
      const inheritancePart = classMatch[2];

      currentClass = {
        name: className,
        attributes: [],
        methods: [],
        visibility: 'public' // Python doesn't have visibility modifiers like Java
      };

      // Parse inheritance
      if (inheritancePart) {
        const parents = inheritancePart.split(',').map(p => p.trim()).filter(p => p && p !== 'object');
        if (parents.length > 0) {
          currentClass.extends = parents[0]; // Primary inheritance
        }
      }

      // Calculate indent level for class body
      const leadingSpaces = originalLine.length - originalLine.trimStart().length;
      indentLevel = leadingSpaces;
      inMethod = false;
      continue;
    }

    // If we have a current class, parse its contents
    if (currentClass) {
      const lineIndent = originalLine.length - originalLine.trimStart().length;

      // If we're still inside the class (same or greater indent)
      if (lineIndent >= indentLevel + 4) { // Python typically uses 4 spaces

        // Check for method definition
        const methodMatch = line.match(/^def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:/);
        if (methodMatch) {
          const methodName = methodMatch[1];
          const parameters = methodMatch[2];
          const returnTypeHint = methodMatch[3];

          // Parse parameters with type hints
          let paramString = '';
          if (parameters && parameters.trim()) {
            const params = parameters.split(',').map(p => {
              const param = p.trim();
              if (param === 'self' || param === 'cls') return ''; // Skip self/cls parameters

              // Enhanced parameter parsing with type hints
              const paramMatch = param.match(/(\w+)(?:\s*:\s*([^=]+))?(?:\s*=\s*(.+))?/);
              if (paramMatch) {
                const paramName = paramMatch[1];
                let paramType = paramMatch[2] || 'Any';

                // Clean up type hints
                paramType = paramType.trim();

                // Convert common Python types to more readable format
                const typeMapping: { [key: string]: string } = {
                  'str': 'String',
                  'int': 'Integer',
                  'float': 'Float',
                  'bool': 'Boolean',
                  'list': 'List',
                  'dict': 'Dictionary',
                  'tuple': 'Tuple',
                  'set': 'Set',
                  'None': 'None'
                };

                if (typeMapping[paramType]) {
                  paramType = typeMapping[paramType];
                } else if (paramType.startsWith('List[') || paramType.startsWith('list[')) {
                  paramType = 'List';
                } else if (paramType.startsWith('Dict[') || paramType.startsWith('dict[')) {
                  paramType = 'Dictionary';
                } else if (paramType.startsWith('Tuple[') || paramType.startsWith('tuple[')) {
                  paramType = 'Tuple';
                }

                return `${paramName}: ${paramType}`;
              }
              return param;
            }).filter(p => p); // Remove empty strings
            paramString = params.join(', ');
          }

          // Determine return type
          let returnType = 'void';
          if (returnTypeHint) {
            returnType = returnTypeHint.trim();
            const typeMapping: { [key: string]: string } = {
              'str': 'String',
              'int': 'Integer',
              'float': 'Float',
              'bool': 'Boolean',
              'None': 'void'
            };
            if (typeMapping[returnType]) {
              returnType = typeMapping[returnType];
            }
          }

          if (methodName === '__init__') {
            currentClass.methods.push(`+ ${currentClass.name}(${paramString})`);
          } else if (!methodName.startsWith('_')) {
            // Public methods
            if (returnType === 'void') {
              currentClass.methods.push(`+ ${methodName}(${paramString})`);
            } else {
              currentClass.methods.push(`+ ${methodName}(${paramString}): ${returnType}`);
            }
          } else if (methodName.startsWith('__') && methodName.endsWith('__')) {
            // Special methods (dunder methods) - include some important ones
            if (['__str__', '__repr__', '__eq__', '__hash__'].includes(methodName)) {
              if (returnType === 'void') {
                currentClass.methods.push(`+ ${methodName}(${paramString})`);
              } else {
                currentClass.methods.push(`+ ${methodName}(${paramString}): ${returnType}`);
              }
            }
          }

          inMethod = true;
          methodIndentLevel = lineIndent;
          continue;
        }

        // Check for class attributes (outside methods)
        if (!inMethod && lineIndent >= indentLevel + 4) {
          const attrMatch = line.match(/^(\w+)\s*:\s*([^=]+)$/);
          if (attrMatch) {
            const attrName = attrMatch[1];
            const typeHint = attrMatch[2].trim();

            // Convert type hints
            let typeHintDisplay = typeHint;
            const typeMapping: { [key: string]: string } = {
              'str': 'String',
              'int': 'Integer',
              'float': 'Float',
              'bool': 'Boolean',
              'list': 'List',
              'dict': 'Dictionary',
              'tuple': 'Tuple',
              'set': 'Set'
            };

            if (typeMapping[typeHint]) {
              typeHintDisplay = typeMapping[typeHint];
            } else if (typeHint.startsWith('List[') || typeHint.startsWith('list[')) {
              typeHintDisplay = 'List';
            } else if (typeHint.startsWith('Dict[') || typeHint.startsWith('dict[')) {
              typeHintDisplay = 'Dictionary';
            }

            currentClass.attributes.push(`# ${attrName}: ${typeHintDisplay}`);
            continue;
          }

          // Check for attribute assignment (self.attribute = value) inside __init__
          const instanceAttrMatch = line.match(/^self\.(\w+)\s*=\s*(.+?)(?:\s*#.*)?$/);
          if (instanceAttrMatch && inMethod) {
            const attrName = instanceAttrMatch[1];
            const assignmentValue = instanceAttrMatch[2];

            // Get type hint from assignment value
            let typeHint = inferPythonType(assignmentValue, line);

            // Check if we already have this attribute
            const existingAttrIndex = currentClass.attributes.findIndex(attr => attr.includes(`${attrName}:`));
            if (existingAttrIndex === -1) {
              currentClass.attributes.push(`- ${attrName}: ${typeHint}`);
            }
          }
        }

        // Check if we've exited a method
        if (inMethod && lineIndent <= methodIndentLevel && line && !line.startsWith(' ') && !line.startsWith('\t')) {
          inMethod = false;
          methodIndentLevel = 0;
        }

      } else if (lineIndent <= indentLevel && line !== '') {
        // We've exited the class, save it
        classes.push(currentClass);
        currentClass = null;
        inMethod = false;
      }
    }
  }

  // Save the last class if exists
  if (currentClass) {
    classes.push(currentClass);
  }

  return classes;
}

/**
 * Parse Java code and extract class information
 */
function parseJavaCode(code: string): ParsedClass[] {
  const classes: ParsedClass[] = [];
  const lines = code.split('\n');

  let currentClass: ParsedClass | null = null;
  let inClass = false;
  let braceCount = 0;
  let classStartLine = -1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const originalLine = lines[i];

    // Skip empty lines and comments
    if (!line || line.startsWith('//') || line.startsWith('/*') || line.startsWith('*')) continue;

    // Check for class or interface definition
    const classMatch = line.match(/^(public\s+|private\s+|protected\s+|)?(?:abstract\s+|final\s+|static\s+|)?(?:class|interface|enum)\s+(\w+)(\s+extends\s+[\w\s,<>.]+)?(\s+implements\s+[\w\s,<>.]+)?\s*\{?/);
    if (classMatch) {
      // Save previous class if exists
      if (currentClass) {
        classes.push(currentClass);
      }

      const visibility = classMatch[1]?.trim();
      const isAbstract = line.includes('abstract');
      const isInterface = line.includes('interface') || line.includes('enum');
      const className = classMatch[2];
      const extendsPart = classMatch[3];
      const implementsPart = classMatch[4];

      currentClass = {
        name: className,
        attributes: [],
        methods: [],
        isAbstract: isAbstract || isInterface,
        visibility: visibility as 'public' | 'private' | 'protected' | 'package' || 'public'
      };

      // Parse extends
      if (extendsPart) {
        const extendsMatch = extendsPart.match(/extends\s+([\w\s,<>.]+)/);
        if (extendsMatch) {
          const parents = extendsMatch[1].split(',').map(p => p.trim()).filter(p => p && !p.includes('<') && !p.includes('>'));
          if (parents.length > 0) {
            currentClass.extends = parents[0];
          }
        }
      }

      // Parse implements
      if (implementsPart) {
        const implementsMatch = implementsPart.match(/implements\s+([\w\s,<>.]+)/);
        if (implementsMatch) {
          currentClass.implements = implementsMatch[1].split(',').map(i => i.trim()).filter(i => i && !i.includes('<') && !i.includes('>'));
        }
      }

      inClass = true;
      classStartLine = i;
      braceCount = (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length;
      continue;
    }

    // If we're inside a class
    if (inClass && currentClass) {
      // Count braces to know when we exit the class
      braceCount += (line.match(/\{/g) || []).length;
      braceCount -= (line.match(/\}/g) || []).length;

      // Check for field declarations (more comprehensive)
      const fieldMatch = line.match(/^(public\s+|private\s+|protected\s+|)(static\s+|final\s+|transient\s+|volatile\s+|)([\w<>[\]\.\s]+)\s+(\w+)(\s*=.*)?;/);
      if (fieldMatch && !line.includes('(') && !line.includes(')') && !line.includes('class') && !line.includes('interface')) {
        const visibility = fieldMatch[1].trim();
        const modifiers = fieldMatch[2].trim();
        const type = fieldMatch[3].trim();
        const name = fieldMatch[4];

        let visibilitySymbol = '';
        if (visibility.includes('public')) visibilitySymbol = '+';
        else if (visibility.includes('private')) visibilitySymbol = '-';
        else if (visibility.includes('protected')) visibilitySymbol = '#';
        else visibilitySymbol = '~'; // package-private

        // Clean up the type (remove extra spaces and generic parameters for display)
        const cleanType = type.replace(/\s+/g, ' ').trim();
        const attrString = `${visibilitySymbol} ${name}: ${cleanType}`;
        currentClass.attributes.push(attrString);
        continue;
      }

      // Check for method declarations and constructors (more comprehensive)
      const methodMatch = line.match(/^(public\s+|private\s+|protected\s+|)(static\s+|abstract\s+|final\s+|synchronized\s+|native\s+|)([\w<>[\],\.\s]*?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*(\{|\;|throws|$)/);
      if (methodMatch && !line.includes('class') && !line.includes('interface') && !line.includes('enum')) {
        const visibility = methodMatch[1].trim();
        const modifiers = methodMatch[2].trim();
        const returnType = methodMatch[3].trim();
        const methodName = methodMatch[4];
        const parameters = methodMatch[5];

        let visibilitySymbol = '';
        if (visibility.includes('public')) visibilitySymbol = '+';
        else if (visibility.includes('private')) visibilitySymbol = '-';
        else if (visibility.includes('protected')) visibilitySymbol = '#';
        else visibilitySymbol = '~'; // package-private

        // Parse parameters more accurately
        let paramString = '';
        if (parameters && parameters.trim()) {
          const params = parameters.split(',').map(p => {
            const paramMatch = p.trim().match(/(?:final\s+)?([\w<>[\],\.\s]+)\s+(\w+)(\[\])?/);
            if (paramMatch) {
              const paramType = paramMatch[1].trim().replace(/\s+/g, ' ');
              const paramName = paramMatch[2];
              const isArray = paramMatch[3];
              return `${paramName}: ${paramType}${isArray || ''}`;
            }
            return p.trim();
          }).filter(p => p);
          paramString = params.join(', ');
        }

        // Check if it's a constructor
        const isConstructor = methodName === currentClass.name && !returnType;
        const isAbstract = modifiers.includes('abstract');

        if (isConstructor) {
          currentClass.methods.push(`${visibilitySymbol} ${methodName}(${paramString})`);
        } else if (returnType && !methodName.startsWith('get') && !methodName.startsWith('set') && !methodName.startsWith('is')) {
          const abstractPrefix = isAbstract ? '«abstract» ' : '';
          const cleanReturnType = returnType.replace(/\s+/g, ' ').trim();
          currentClass.methods.push(`${abstractPrefix}${visibilitySymbol} ${methodName}(${paramString}): ${cleanReturnType}`);
        }
        continue;
      }

      // If brace count reaches 0, we've exited the class
      if (braceCount <= 0) {
        classes.push(currentClass);
        currentClass = null;
        inClass = false;
        classStartLine = -1;
      }
    }
  }

  // Save the last class if exists
  if (currentClass) {
    classes.push(currentClass);
  }

  return classes;
}

/**
 * Infer Python type from assignment or type hint
 */
function inferPythonType(value: string, line?: string): string {
  // First check if we have a type hint in the line (for attributes)
  if (line) {
    const typeHintMatch = line.match(/#\s*(?:protected\s+)?(?:attribute\s*\(\s*)?(\w+)/i);
    if (typeHintMatch) {
      const hint = typeHintMatch[1].toLowerCase();
      switch (hint) {
        case 'string':
        case 'str': return 'String';
        case 'int':
        case 'integer': return 'Integer';
        case 'float':
        case 'double': return 'Float';
        case 'bool':
        case 'boolean': return 'Boolean';
        case 'list': return 'List';
        case 'dict':
        case 'dictionary': return 'Dictionary';
      }
    }
  }

  // Clean the value
  const cleanValue = value?.trim();

  if (!cleanValue) return 'Any';

  // Check for common patterns
  if (cleanValue.startsWith('"') || cleanValue.startsWith("'")) return 'String';
  if (cleanValue.match(/^\d+$/)) return 'Integer';
  if (cleanValue.match(/^\d+\.\d*$/)) return 'Float';
  if (cleanValue.toLowerCase() === 'true' || cleanValue.toLowerCase() === 'false') return 'Boolean';
  if (cleanValue.startsWith('[') && cleanValue.endsWith(']')) return 'List';
  if (cleanValue.startsWith('{') && cleanValue.endsWith('}')) return 'Dictionary';
  if (cleanValue === 'None') return 'None';

  // Check for class instantiations (e.g., Animal(), Dog("name"))
  const classMatch = cleanValue.match(/^([A-Z]\w*)\s*\(/);
  if (classMatch) {
    return classMatch[1]; // Return the class name
  }

  // Default to object or unknown
  return 'Any';
}

/**
 * Analyze relationships between classes - Ultra Comprehensive Analysis
 * تحليل شامل لجميع العلاقات الممكنة بين الكلاسات
 * - فحص كل كلاس بدقة تامة
 * - عدم حذف أي علاقة مهما كانت
 * - اكتشاف العلاقات من الخصائص والطرق والمعاملات
 */
function analyzeRelationships(classes: ParsedClass[]): ClassRelationship[] {
  const relationships: ClassRelationship[] = [];

  console.log('🔍 بدء التحليل الشامل للعلاقات...');
  console.log('📊 عدد الكلاسات المراد تحليلها:', classes.length);

  classes.forEach(cls => {
    console.log(`\n🔍 تحليل الكلاس: ${cls.name}`);

    // 1. وراثة (Inheritance)
    if (cls.extends) {
      console.log(`  📈 وراثة مكتشفة: ${cls.name} extends ${cls.extends}`);

      relationships.push({
        from: cls.name,
        to: cls.extends,
        type: 'inheritance'
      });

      console.log(`  ✅ أضيفت علاقة الوراثة: ${cls.name} <|-- ${cls.extends}`);
    }

    // 2. تنفيذ الواجهات (Interface Implementation)
    if (cls.implements && cls.implements.length > 0) {
      console.log(`  🔗 تنفيذ واجهات: ${cls.implements.join(', ')}`);

      cls.implements.forEach(interfaceName => {
        relationships.push({
          from: cls.name,
          to: interfaceName,
          type: 'implementation'
        });
        console.log(`  ✅ أضيفت علاقة التنفيذ: ${cls.name} <|.. ${interfaceName}`);
      });
    }

    // 3. تحليل الخصائص (Attributes Analysis)
    console.log(`  📋 تحليل الخصائص (${cls.attributes.length} خاصية)...`);

    cls.attributes.forEach((attr, attrIndex) => {
      console.log(`    ${attrIndex + 1}. تحليل الخاصية: ${attr}`);

      // استخراج اسم ونوع الخاصية
      const attrMatch = attr.match(/^([-+#~])\s+(.+?):\s*(.+)$/);
      if (attrMatch) {
        const visibility = attrMatch[1];
        const attrName = attrMatch[2].trim();
        const attrType = attrMatch[3].trim();

        console.log(`      👁️  الاسم: ${attrName}, النوع: ${attrType}`);

        // البحث عن علاقات مع جميع الكلاسات الأخرى
        classes.forEach(otherClass => {
          if (otherClass.name !== cls.name) {
            // فحص أي إشارة للكلاس الآخر
            const typePatterns = [
              ` ${otherClass.name}`, // Space before to avoid partial matches
              `${otherClass.name}<`,
              `${otherClass.name}>`,
              `${otherClass.name}[`,
              `${otherClass.name}]`,
              `${otherClass.name}(`,
              `${otherClass.name})`,
              `${otherClass.name};`,
              `${otherClass.name} `,
              ` ${otherClass.name} `,
            ];

            const hasRelationship = typePatterns.some(pattern =>
              attrType.includes(pattern) ||
              attrType === otherClass.name ||
              attrType.endsWith(otherClass.name) ||
              attrType.startsWith(otherClass.name)
            );

            if (hasRelationship) {
              console.log(`      🎯 علاقة مكتشفة مع كلاس ${otherClass.name} عبر الخاصية ${attrName}`);

              // تحديد نوع العلاقة
              let relationshipType: 'composition' | 'aggregation' | 'association' = 'association';

              // قائمة الكلمات المفتاحية لتحديد نوع العلاقة
              const compositionKeywords = [
                'engine', 'wheel', 'door', 'window', 'roof', 'floor', 'heart', 'brain',
                'owns', 'contains', 'has', 'manages', 'controls', 'possesses', 'belongs',
                'member', 'employee', 'student', 'teacher', 'driver', 'pilot'
              ];

              const aggregationKeywords = [
                'list', 'array', 'collection', 'set', 'map', 'group', 'bundle',
                'members', 'items', 'elements', 'parts', 'components', 'pieces',
                'children', 'siblings', 'friends', 'colleagues', 'team', 'group',
                'family', 'class', 'students', 'employees', 'workers', 'staff'
              ];

              const lowerAttrName = attrName.toLowerCase();
              const lowerAttrType = attrType.toLowerCase();

              // Composition (تملك - معين مملوء)
              if (compositionKeywords.some(keyword =>
                lowerAttrName.includes(keyword) ||
                lowerAttrType.includes(keyword)
              ) || (attrType === otherClass.name)) {
                relationshipType = 'composition';
                console.log(`        ✅ نوع العلاقة: Composition (*--)`);
              }
              // Aggregation (تجميع - معين مفرغ)
              else if (aggregationKeywords.some(keyword =>
                lowerAttrName.includes(keyword) ||
                lowerAttrType.includes(keyword) ||
                attrType.includes('List<') ||
                attrType.includes('Array<') ||
                attrType.includes('Collection<') ||
                attrType.includes('Set<') ||
                attrType.includes('Map<') ||
                attrType.includes('[]') ||
                attrType.includes('List') ||
                attrType.includes('Array') ||
                attrType.includes('Collection')
              )) {
                relationshipType = 'aggregation';
                console.log(`        ✅ نوع العلاقة: Aggregation (o--)`);
              }
              // Association (ارتباط)
              else {
                relationshipType = 'association';
                console.log(`        ✅ نوع العلاقة: Association (-->)`);
              }

              // تجنب العلاقات المكررة
              const existingRelationship = relationships.find(rel =>
                rel.from === cls.name && rel.to === otherClass.name && rel.type === relationshipType
              );

              if (!existingRelationship) {
                relationships.push({
                  from: cls.name,
                  to: otherClass.name,
                  type: relationshipType,
                  label: attrName
                });

                console.log(`      ✅ تمت إضافة العلاقة: ${cls.name} ${getArrowSymbol(relationshipType)} ${otherClass.name}`);
              }
            }
          }
        });
      }
    });

    // 4. تحليل معاملات الطرق (Method Parameters Analysis)
    console.log(`  🔧 تحليل معاملات الطرق (${cls.methods.length} طريقة)...`);

    cls.methods.forEach((method, methodIndex) => {
      console.log(`    ${methodIndex + 1}. تحليل الطريقة: ${method}`);

      const methodMatch = method.match(/^([-+#~])\s+(\w+)\(([^)]*)\)/);
      if (methodMatch) {
        const methodName = methodMatch[2];
        const params = methodMatch[3];

        if (params && params.trim()) {
          console.log(`      📝 المعاملات: ${params}`);

          const paramList = params.split(',').map(p => p.trim());
          paramList.forEach(param => {
            const paramMatch = param.match(/(\w+):\s*(.+)/);
            if (paramMatch) {
              const paramName = paramMatch[1];
              const paramType = paramMatch[2].trim();

              console.log(`        🔍 معامل: ${paramName} من نوع ${paramType}`);

              // البحث عن علاقات مع كلاسات أخرى عبر المعاملات
              classes.forEach(otherClass => {
                if (otherClass.name !== cls.name && (
                  paramType === otherClass.name ||
                  paramType.includes(` ${otherClass.name}`) ||
                  paramType.includes(`${otherClass.name}<`) ||
                  paramType.includes(`${otherClass.name}>`)
                )) {
                  console.log(`        🎯 علاقة عبر معامل: ${cls.name} --> ${otherClass.name}`);

                  // تجنب العلاقات المكررة
                  const existingRelationship = relationships.find(rel =>
                    rel.from === cls.name && rel.to === otherClass.name && rel.type === 'dependency'
                  );

                  if (!existingRelationship) {
                    relationships.push({
                      from: cls.name,
                      to: otherClass.name,
                      type: 'dependency',
                      label: `${methodName}(${paramName})`
                    });

                    console.log(`        ✅ تمت إضافة العلاقة (dependency): ${cls.name} ..> ${otherClass.name}`);
                  }
                }
              });
            }
          });
        }
      }
    });

    console.log(`  ✅ انتهى تحليل الكلاس: ${cls.name}`);
  });

  console.log('\n🧹 مراجعة العلاقات النهائية...');
  console.log(`📊 تم العثور على ${relationships.length} علاقة:`);

  relationships.forEach((rel, index) => {
    const arrowSymbol = getArrowSymbol(rel.type);
    const labelText = rel.label ? ` : ${rel.label}` : '';
    console.log(`  ${index + 1}. ${rel.from} ${arrowSymbol} ${rel.to}${labelText}`);
  });

  const typeStats = relationships.reduce((acc, rel) => {
    acc[rel.type] = (acc[rel.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  console.log(`\n📈 إحصائيات التحليل:`);
  Object.entries(typeStats).forEach(([type, count]) => {
    console.log(`  • ${type}: ${count}`);
  });

  console.log('\n🎯 التحليل مكتمل!');

  // Normalize relationships (keep the most important type when duplicates exist)
  const finalRelationships = normalizeRelationships(relationships);
  console.log(`🔁 بعد توحيد العلاقات تم الحصول على ${finalRelationships.length} علاقة`);

  return finalRelationships;
}

// Normalize helper used to pick highest-priority relation when duplicates exist
function normalizeRelationships(rels: ClassRelationship[]): ClassRelationship[] {
  const priority: Record<string, number> = {
    'inheritance': 6,
    'implementation': 5,
    'composition': 4,
    'aggregation': 3,
    'association': 2,
    'dependency': 1
  };

  const map = new Map<string, ClassRelationship>();
  rels.forEach(r => {
    const key = `${r.from}|||${r.to}|||${r.label || ''}`;
    const existing = map.get(key);
    if (!existing) map.set(key, r);
    else if ((priority[r.type] || 0) > (priority[existing.type] || 0)) map.set(key, r);
  });

  return Array.from(map.values());
}

// مساعد للحصول على رمز السهم
function getArrowSymbol(type: string): string {
  switch (type) {
    case 'inheritance': return '--|>';
    case 'implementation': return '..|>';
    case 'composition': return '--*';
    case 'aggregation': return '--o';
    case 'dependency': return '..>';
    case 'association': return '-->';
    default: return '-->';
  }
}

/**
 * Main function to parse code and generate diagram data
 */
export function parseCodeToDiagram(
  code: string,
  language: 'python' | 'java',
  codeName: string,
  fileName: string
): DiagramData {
  let classes: ParsedClass[] = [];
  let relationships: ClassRelationship[] = [];

  try {
    if (language === 'python') {
      classes = parsePythonCode(code);
    } else if (language === 'java') {
      classes = parseJavaCode(code);
    }

    // Analyze relationships between classes
    relationships = analyzeRelationships(classes);

    // If no classes found, create a placeholder
    if (classes.length === 0) {
      classes = [{
        name: 'NoClassesFound',
        attributes: ['# message: No classes detected in the code'],
        methods: ['+ analyze(): void']
      }];
    }

  } catch (error) {
    console.error('Error parsing code:', error);
    classes = [{
      name: 'ParseError',
      attributes: [`# error: ${(error as Error).message}`],
      methods: ['+ retry(): void']
    }];
  }

  return {
    title: `Class Diagram - ${codeName}`,
    description: `Generated from ${fileName} (${language}). Found ${classes.length} class(es) and ${relationships.length} relationship(s).`,
    classes,
    relationships
  };
}