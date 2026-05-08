/**
 * محلل دقيق للكود يستخرج بيانات مخطط الكلاسات بصيغة JSON
 * مع الالتزام الصارم بالقواعد المحددة لضمان التطابق 100%
 */

export interface ClassData {
  name: string;
  attributes: string[];
  methods: string[];
  extends?: string;
  implements?: string[];
}

export interface Relationship {
  from: string;
  to: string;
  type: 'inheritance' | 'implementation' | 'composition' | 'aggregation' | 'association' | 'dependency';
  label?: string;
}

export interface ClassDiagramData {
  classes: ClassData[];
  relationships: Relationship[];
}

/**
 * محلل دقيق لكود Java - يستخرج جميع التفاصيل بدقة 100%
 */
export function analyzeJavaCode(code: string): ClassDiagramData {
  const classes: ClassData[] = [];
  const relationships: Relationship[] = [];
  // Register class names early so fields/params can reference classes declared later
  const classNames: Set<string> = new Set<string>();

  // تقسيم الكود إلى أسطر
  const lines = code.split('\n');
  let currentClass: ClassData | null = null;
  let braceCount = 0;
  let inClass = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // تخطي التعليقات والسطور الفارغة
    if (!line || line.startsWith('//') || line.startsWith('/*') || line.startsWith('*')) continue;

    // البحث عن تعريف كلاس
    const classMatch = line.match(/^(?:public\s+|private\s+|protected\s+|)?(?:abstract\s+|final\s+|static\s+|)?(?:class|interface|enum)\s+(\w+)(?:\s+extends\s+([\w\s,<>.]+))?(?:\s+implements\s+([\w\s,<>.]+))?\s*\{?/);
    if (classMatch) {
      // حفظ الكلاس السابق إذا وجد
      if (currentClass) {
        classes.push(currentClass);
      }

      const className = classMatch[1];
      const extendsPart = classMatch[2];
      const implementsPart = classMatch[3];

      currentClass = {
        name: className,
        attributes: [],
        methods: []
      };

      // سجل اسم الكلاس فورًا لتمكين اكتشاف العلاقات مع كائنات معرفة لاحقًا
      classNames.add(className);

      // معالجة الوراثة (extends)
      if (extendsPart) {
        const parents = extendsPart.split(',').map(p => p.trim()).filter(p => p && !p.includes('<') && !p.includes('>'));
        if (parents.length > 0) {
          currentClass.extends = parents[0];

          // إضافة علاقة الوراثة - الابن يرث من الأب
          relationships.push({
            from: className, // الابن
            to: parents[0],  // الأب
            type: 'inheritance'
          });
        }
      }

      // معالجة التنفيذ (implements)
      if (implementsPart) {
        const impls = implementsPart.split(',').map(i => i.trim()).filter(i => i && !i.includes('<') && !i.includes('>'));
        if (impls.length > 0) {
          currentClass.implements = impls;

          // إضافة علاقات التنفيذ كـ implementation
          currentClass.implements.forEach(interfaceName => {
            relationships.push({
              from: className,
              to: interfaceName,
              type: 'implementation'
            });
          });
        }
      }

      inClass = true;
      braceCount = (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length;
      continue;
    }

    // إذا كنا داخل كلاس
    if (inClass && currentClass) {
      // عد الأقواس
      braceCount += (line.match(/\{/g) || []).length;
      braceCount -= (line.match(/\}/g) || []).length;

      // البحث عن خصائص الكلاس (fields)
      const fieldMatch = line.match(/^(public\s+|private\s+|protected\s+|)(?:static\s+|final\s+|transient\s+|volatile\s+|)([\w<>[\]\.\s]+)\s+(\w+)(\s*=.*)?;/);
      if (fieldMatch && !line.includes('(') && !line.includes(')') && !line.includes('class') && !line.includes('interface') && !line.includes('enum')) {
        const visibility = fieldMatch[1].trim();
        const type = fieldMatch[2].trim();
        const name = fieldMatch[3];

        let visibilitySymbol = '';
        if (visibility.includes('public')) visibilitySymbol = '+';
        else if (visibility.includes('private')) visibilitySymbol = '-';
        else if (visibility.includes('protected')) visibilitySymbol = '#';
        else visibilitySymbol = '~'; // package-private

        const cleanType = type.replace(/\s+/g, ' ').trim();
        currentClass.attributes.push(`${visibilitySymbol} ${name}: ${cleanType}`);

        // تحليل العلاقات بناءً على نوع الخاصية (تمرير قائمة الأسماء)
        analyzeFieldRelationships(currentClass.name, name, cleanType, relationships, classNames);
      }

      // البحث عن الطرق والconstructors
      const methodMatch = line.match(/^(public\s+|private\s+|protected\s+|)(?:static\s+|abstract\s+|final\s+|synchronized\s+|native\s+|)([\w<>[\],\.\s]*?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*(\{|\;|throws|$)/);
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
        else visibilitySymbol = '~';

        // معالجة المعاملات
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

        const isConstructor = methodName === currentClass.name && !returnType;
        const isAbstract = modifiers.includes('abstract');

        if (isConstructor) {
          currentClass.methods.push(`${visibilitySymbol} ${methodName}(${paramString})`);
        } else if (returnType && !methodName.startsWith('get') && !methodName.startsWith('set') && !methodName.startsWith('is')) {
          const abstractPrefix = isAbstract ? '«abstract» ' : '';
          const cleanReturnType = returnType.replace(/\s+/g, ' ').trim();
          currentClass.methods.push(`${abstractPrefix}${visibilitySymbol} ${methodName}(${paramString}): ${cleanReturnType}`);
        }

        // تحليل علاقات المعاملات (تعاملها كـ dependencies)
        if (parameters && parameters.trim()) {
          analyzeParameterRelationships(currentClass.name, methodName, parameters, relationships, classNames);
        }
      }

      // إنهاء الكلاس
      if (braceCount <= 0) {
        classes.push(currentClass);
        currentClass = null;
        inClass = false;
      }
    }
  }

  // حفظ الكلاس الأخير
  if (currentClass) {
    classes.push(currentClass);
  }

  return { classes, relationships };
}

/**
 * تحليل علاقات الخصائص (fields)
 */
function analyzeFieldRelationships(className: string, fieldName: string, fieldType: string, relationships: Relationship[], classNames: Set<string>) {
  // استخراج الأسماء المحتملة من النوع: ClassName أو List<ClassName> أو ClassName[] أو Map<Key,ClassName>
  const candidates: Set<string> = new Set<string>();
  const regex = /([A-Z][A-Za-z0-9_]*)/g;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(fieldType)) !== null) {
    candidates.add(m[1]);
  }

  candidates.forEach(candidate => {
    if (candidate !== className && classNames.has(candidate)) {
      // تحديد نوع العلاقة
      let relationshipType: 'composition' | 'aggregation' | 'association' = 'association';

      // إذا كان النوع متطابقًا تمامًا (مثلاً "Engine") -> composition
      if (fieldType === candidate) {
        relationshipType = 'composition';
      } else if (fieldType.includes('List<') || fieldType.includes('ArrayList<') ||
                 fieldType.includes('Set<') || fieldType.includes('Collection<') ||
                 fieldType.includes('Map<') || fieldType.includes('[]') || fieldType.toLowerCase().includes('list') ) {
        relationshipType = 'aggregation';
      }

      // تجنب التكرار
      const existingRelationship = relationships.find(rel =>
        rel.from === className && rel.to === candidate && rel.type === relationshipType && rel.label === fieldName
      );

      if (!existingRelationship) {
        relationships.push({
          from: className,
          to: candidate,
          type: relationshipType,
          label: fieldName
        });
      }
    }
  });
}

/**
 * تحليل علاقات المعاملات (parameters)
 */
function analyzeParameterRelationships(className: string, methodName: string, parameters: string, relationships: Relationship[], classNames: Set<string>) {
  const paramList = parameters.split(',');

  paramList.forEach(param => {
    const paramMatch = param.trim().match(/(?:final\s+)?([\w<>[\],\.\s]+)\s+(\w+)(\[\])?/);
    if (paramMatch) {
      const paramType = paramMatch[1].trim();
      const paramName = paramMatch[2];

      // استخراج المرشحين من نوع المعامل
      const regex = /([A-Z][A-Za-z0-9_]*)/g;
      let m: RegExpExecArray | null;
      const candidates: Set<string> = new Set<string>();
      while ((m = regex.exec(paramType)) !== null) {
        candidates.add(m[1]);
      }

      candidates.forEach(candidate => {
        if (candidate !== className && classNames.has(candidate)) {
          // تجنب التكرار
          const existingRelationship = relationships.find(rel =>
            rel.from === className && rel.to === candidate && rel.type === 'dependency' && rel.label === `${methodName}(${paramName})`
          );

          if (!existingRelationship) {
            relationships.push({
              from: className,
              to: candidate,
              type: 'dependency',
              label: `${methodName}(${paramName})`
            });
          }
        }
      });
    }
  });
}

/**
 * تحليل كود Python
 */
export function analyzePythonCode(code: string): ClassDiagramData {
  const classes: ClassData[] = [];
  const relationships: Relationship[] = [];
  // register class names early for Python as well
  const classNames: Set<string> = new Set<string>();

  const lines = code.split('\n');
  let currentClass: ClassData | null = null;
  let indentLevel = 0;
  let inMethod = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const originalLine = lines[i];

    if (!line || line.startsWith('#')) continue;

    // البحث عن تعريف كلاس
    const classMatch = line.match(/^class\s+(\w+)(?:\(([^)]*)\))?:/);
    if (classMatch) {
      if (currentClass) {
        classes.push(currentClass);
      }

      const className = classMatch[1];
      const inheritancePart = classMatch[2];

      currentClass = {
        name: className,
        attributes: [],
        methods: []
      };

      // سجل اسم الكلاس فورًا لتمكين اكتشاف العلاقات مع كائنات معرفة لاحقًا
      classNames.add(className);

      // معالجة الوراثة
      if (inheritancePart) {
        const parents = inheritancePart.split(',').map(p => p.trim()).filter(p => p && p !== 'object');
        if (parents.length > 0) {
          currentClass.extends = parents[0];
          relationships.push({
            from: className,
            to: parents[0],
            type: 'inheritance'
          });
        }
      }

      indentLevel = originalLine.length - originalLine.trimStart().length;
      inMethod = false;
      continue;
    }

    // إذا كنا داخل كلاس
    if (currentClass && originalLine.length - originalLine.trimStart().length >= indentLevel + 4) {
      // البحث عن الطرق
      const methodMatch = line.match(/^def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:/);
      if (methodMatch) {
        const methodName = methodMatch[1];
        const parameters = methodMatch[2];
        const returnTypeHint = methodMatch[3];

        let paramString = '';
        if (parameters && parameters.trim()) {
          const params = parameters.split(',').map(p => {
            const param = p.trim();
            if (param === 'self' || param === 'cls') return '';

            const paramMatch = param.match(/(\w+)(?:\s*:\s*([^=]+))?(?:\s*=\s*(.+))?/);
            if (paramMatch) {
              const paramName = paramMatch[1];
              let paramType = paramMatch[2] || 'Any';
              return `${paramName}: ${paramType}`;
            }
            return param;
          }).filter(p => p);
          paramString = params.join(', ');
        }

        let returnType = 'void';
        if (returnTypeHint) {
          returnType = returnTypeHint.trim();
        }

        if (methodName === '__init__') {
          currentClass.methods.push(`+ ${currentClass.name}(${paramString})`);
        } else {
          currentClass.methods.push(`+ ${methodName}(${paramString}): ${returnType}`);
        }

        // تحليل علاقات المعاملات (تعاملها كـ dependencies)
        if (parameters && parameters.trim()) {
          analyzePythonParameterRelationships(currentClass.name, methodName, parameters, relationships, classNames);
        }

        inMethod = true;
        continue;
      }

      // البحث عن الخصائص في __init__
      if (inMethod && line.match(/^self\.(\w+)\s*=\s*(.+?)(?:\s*#.*)?$/)) {
        const attrMatch = line.match(/^self\.(\w+)\s*=\s*(.+?)(?:\s*#.*)?$/);
        if (attrMatch) {
          const attrName = attrMatch[1];
          const assignmentValue = attrMatch[2];

          let attrType = 'Any';
          if (assignmentValue.includes('str(') || assignmentValue.startsWith('"') || assignmentValue.startsWith("'")) {
            attrType = 'str';
          } else if (assignmentValue.includes('int(') || /^\d+$/.test(assignmentValue)) {
            attrType = 'int';
          } else if (assignmentValue.includes('list(') || assignmentValue.startsWith('[')) {
            attrType = 'List';
          } else if (assignmentValue.includes('dict(') || assignmentValue.startsWith('{')) {
            attrType = 'Dict';
          } else if (assignmentValue.match(/^[A-Z]\w*\s*\(/)) {
            // يبدو أنه إنشاء كائن
            const classMatch = assignmentValue.match(/^([A-Z]\w*)\s*\(/);
            if (classMatch) {
              attrType = classMatch[1];
            }
          }

          currentClass.attributes.push(`- ${attrName}: ${attrType}`);

          // تحليل العلاقات
          analyzePythonFieldRelationships(currentClass.name, attrName, attrType, relationships, classNames);
        }
      }
    }
  }

  if (currentClass) {
    classes.push(currentClass);
  }

  return { classes, relationships };
}

/**
 * تحليل علاقات الخصائص في Python
 */
function analyzePythonFieldRelationships(className: string, fieldName: string, fieldType: string, relationships: Relationship[], classNames: Set<string>) {
  // نوع الحقل قد يكون "List[Wheel]", "Wheel", "list[Wheel]" أو "Wheel()" etc.
  const candidates: Set<string> = new Set<string>();
  const regex = /([A-Z][A-Za-z0-9_]*)/g;
  let m: RegExpExecArray | null;
  while ((m = regex.exec(fieldType)) !== null) {
    candidates.add(m[1]);
  }

  candidates.forEach(candidate => {
    if (candidate !== className && classNames.has(candidate)) {
      // افتراض: إذا كان النوع مطابقًا للاسم -> composition
      // إذا كان list/[] -> aggregation
      let relationshipType: 'composition' | 'aggregation' | 'association' = 'association';
      if (fieldType === candidate) {
        relationshipType = 'composition';
      } else if (fieldType.includes('[') || fieldType.toLowerCase().includes('list')) {
        relationshipType = 'aggregation';
      }

      const existingRelationship = relationships.find(rel =>
        rel.from === className && rel.to === candidate && rel.type === relationshipType && rel.label === fieldName
      );

      if (!existingRelationship) {
        relationships.push({
          from: className,
          to: candidate,
          type: relationshipType,
          label: fieldName
        });
      }
    }
  });
}

/**
 * تحليل علاقات المعاملات في Python
 */
function analyzePythonParameterRelationships(className: string, methodName: string, parameters: string, relationships: Relationship[], classNames: Set<string>) {
  const paramList = parameters.split(',');

  paramList.forEach(param => {
    const paramMatch = param.trim().match(/(\w+)(?:\s*:\s*([^=]+))?(?:\s*=\s*(.+))?/);
    if (paramMatch) {
      const paramName = paramMatch[1];
      const paramType = (paramMatch[2] || '').trim();

      if (paramType) {
        // استخراج المرشحين من نوع المعامل
        const regex = /([A-Z][A-Za-z0-9_]*)/g;
        let m: RegExpExecArray | null;
        const candidates: Set<string> = new Set<string>();
        while ((m = regex.exec(paramType)) !== null) {
          candidates.add(m[1]);
        }

        candidates.forEach(candidate => {
          if (candidate !== className && classNames.has(candidate)) {
            const existingRelationship = relationships.find(rel =>
              rel.from === className && rel.to === candidate && rel.type === 'dependency' && rel.label === `${methodName}(${paramName})`
            );

            if (!existingRelationship) {
              relationships.push({
                from: className,
                to: candidate,
                type: 'dependency',
                label: `${methodName}(${paramName})`
              });
            }
          }
        });
      }
    }
  });
}

/**
 * Normalize relationships and keep highest-priority relation when duplicates exist
 */
function normalizeRelationships(rels: Relationship[]): Relationship[] {
  const priority: Record<string, number> = {
    'inheritance': 6,
    'implementation': 5,
    'composition': 4,
    'aggregation': 3,
    'association': 2,
    'dependency': 1
  };

  const map = new Map<string, Relationship>();
  rels.forEach(r => {
    const key = `${r.from}|||${r.to}|||${r.label || ''}`;
    const existing = map.get(key);
    if (!existing) {
      map.set(key, r);
    } else {
      // keep highest priority
      if ((priority[r.type] || 0) > (priority[existing.type] || 0)) {
        map.set(key, r);
      }
    }
  });

  return Array.from(map.values());
}

/**
 * توليد كود Mermaid من البيانات مع معالجة صحيحة للعلاقات UML
 */
export function generateMermaidCode(data: ClassDiagramData): string {
  // 1. تعريف البداية والاتجاه (من الأعلى للأسفل يوضح الوراثة بشكل أفضل)
  let mermaidCode = 'classDiagram\n';
  mermaidCode += '    direction TB\n\n';

  // 2. معالجة الكلاسات (Classes, Methods, Attributes)
  if (data.classes) {
    data.classes.forEach((cls: any) => {
      // تنظيف اسم الكلاس من أي رموز غير مسموحة
      const className = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');

      mermaidCode += `    class ${className} {\n`;

      // إضافة الخصائص (Attributes)
      if (cls.attributes && cls.attributes.length > 0) {
        cls.attributes.forEach((attr: any) => {
          const attrName = typeof attr === 'string' ? attr : attr.name;
          mermaidCode += `        ${attrName}\n`;
        });
      }

      // إضافة الميثودز (Methods)
      if (cls.methods && cls.methods.length > 0) {
        cls.methods.forEach((method: any) => {
          // التأكد من وجود الأقواس للميثود لتبدو احترافية
          const methodStr = method.includes('(') ? method : `${method}()`;
          mermaidCode += `        ${methodStr}\n`;
        });
      }
      mermaidCode += '    }\n\n';

      // معالجة الوراثة إذا كانت موجودة داخل كائن الكلاس نفسه (Legacy Support)
      if (cls.inherits) {
        const parents = Array.isArray(cls.inherits) ? cls.inherits : [cls.inherits];
        parents.forEach((parent: string) => {
          const parentName = parent.replace(/[^a-zA-Z0-9_]/g, '_');
          mermaidCode += `    ${parentName} <|-- ${className}\n`;
        });
      }
    });
  }

  // 3. معالجة العلاقات المركزية (The Standard UML Logic)
  if (data.relationships) {
    data.relationships.forEach((rel: any) => {
      const from = rel.from.replace(/[^a-zA-Z0-9_]/g, '_');
      const to = rel.to.replace(/[^a-zA-Z0-9_]/g, '_');

      switch (rel.type) {
        case 'inheritance':
          // الابن يشير للأب - السهم يخرج من التابع للأصل
          mermaidCode += `    ${to} <|-- ${from}\n`;
          break;
        case 'implementation':
          // تحقيق الواجهات (سهم متقطع)
          mermaidCode += `    ${to} <|.. ${from}\n`;
          break;
        case 'composition':
          // علاقة ملكية قوية (معين مصمت)
          mermaidCode += `    ${from} *-- ${to}\n`;
          break;
        case 'aggregation':
          // علاقة تجميع (معين مفرغ)
          mermaidCode += `    ${from} o-- ${to}\n`;
          break;
        case 'dependency':
          // تبعية (سهم متقطع)
          mermaidCode += `    ${from} ..> ${to}\n`;
          break;
        case 'association':
        default:
          // ارتباط عادي
          mermaidCode += `    ${from} --> ${to}\n`;
          break;
      }
    });
  }

  return mermaidCode;
}

/**
 * دالة رئيسية لتحليل الكود
 */
export function analyzeCode(code: string, language: 'java' | 'python'): ClassDiagramData {
  if (language === 'java') {
    return analyzeJavaCode(code);
  } else if (language === 'python') {
    return analyzePythonCode(code);
  } else {
    throw new Error(`Unsupported language: ${language}`);
  }
}


