// jsonToMermaid.ts
// Utility to convert JSON class diagram data to Mermaid syntax

interface ClassAttribute {
  name: string;
  type: string;
  visibility: 'public' | 'private' | 'protected';
}

interface MethodParameter {
  name: string;
  type: string;
}

interface ClassMethod {
  name: string;
  signature?: string;  // ✅ Added signature field (actual format from backend)
  parameters?: MethodParameter[];  // Optional for backward compatibility
  return_type?: string;
  visibility: 'public' | 'private' | 'protected';
  is_abstract?: boolean;
  type?: 'method' | 'constructor';
}

interface ClassInfo {
  name: string;
  attributes: ClassAttribute[];
  methods: ClassMethod[];
  is_interface: boolean;
  is_abstract: boolean;
}

interface Relationship {
  from: string;
  to: string;
  type: 'inheritance' | 'aggregation' | 'composition' | 'association';
  label?: string;
}

interface DiagramData {
  classes: ClassInfo[];
  relationships: Relationship[];
}

/**
 * تحويل visibility symbol
 */
const getVisibilitySymbol = (visibility: string): string => {
  switch (visibility) {
    case 'public':
      return '+';
    case 'private':
      return '-';
    case 'protected':
      return '#';
    default:
      return '+';
  }
};

/**
 * تحويل relationship type إلى Mermaid syntax
 */
const getRelationshipSyntax = (type: string): string => {
  switch (type) {
    case 'inheritance':
      return '--|>';
    case 'composition':
      return '--*';
    case 'aggregation':
      return '--o';
    case 'association':
      return '-->';
    default:
      return '-->';
  }
};

/**
 * تنظيف اسم الـ class من الأحرف الخاصة
 */
const sanitizeClassName = (name: string): string => {
  return name.replace(/[^\w]/g, '_');
};

/**
 * تحويل JSON إلى Mermaid class diagram syntax
 */
export const convertJsonToMermaid = (data: DiagramData | string): string => {
  try {
    // إذا كانت البيانات string، حاول parse
    let parsedData: DiagramData;
    if (typeof data === 'string') {
      try {
        parsedData = JSON.parse(data);
      } catch (e) {
        // إذا فشل الـ parse، تحقق إذا كان بالفعل Mermaid code
        if (data.trim().startsWith('classDiagram') || data.trim().startsWith('graph')) {
          return data;
        }
        throw new Error('Invalid JSON data');
      }
    } else {
      parsedData = data;
    }

    // 🔥 فلتر Python built-in classes (لا ينبغي أن تظهر في المخطط)
    const EXCLUDED_CLASSES = new Set([
      'ABC', 'ABCMeta',           // Abstract Base Classes
      'Enum', 'IntEnum', 'Flag', 'IntFlag',  // Enums
      'TypedDict', 'NamedTuple',  // Typing constructs
      'Protocol', 'Generic',      // Typing protocols
      'object', 'type',           // Base types
      'dict', 'list', 'tuple', 'set', 'frozenset',  // Collections
      'str', 'int', 'float', 'bool', 'bytes',  // Primitives
    ]);

    // فلتر الـ classes
    const validClasses = parsedData.classes?.filter(
      c => !EXCLUDED_CLASSES.has(c.name)
    ) || [];

    // فلتر الـ relationships
    const validRelationships = parsedData.relationships?.filter(
      r => !EXCLUDED_CLASSES.has(r.from) && !EXCLUDED_CLASSES.has(r.to)
    ) || [];

    console.log(`🔍 Filtered out ${(parsedData.classes?.length || 0) - validClasses.length} built-in classes`);
    console.log(`🔍 Filtered out ${(parsedData.relationships?.length || 0) - validRelationships.length} built-in relationships`);

    // بداية الـ Mermaid diagram
    let mermaidCode = 'classDiagram\n';

    // إضافة الـ classes
    if (validClasses && Array.isArray(validClasses)) {
      validClasses.forEach((classInfo: ClassInfo) => {
        const className = sanitizeClassName(classInfo.name);

        // إضافة الـ class definition
        if (classInfo.is_abstract) {
          mermaidCode += `    class ${className} {\n`;
          mermaidCode += `        <<abstract>>\n`;
        } else if (classInfo.is_interface) {
          mermaidCode += `    class ${className} {\n`;
          mermaidCode += `        <<interface>>\n`;
        } else {
          mermaidCode += `    class ${className} {\n`;
        }

        // إضافة الـ attributes
        if (classInfo.attributes && Array.isArray(classInfo.attributes)) {
          classInfo.attributes.forEach((attr: ClassAttribute) => {
            const symbol = getVisibilitySymbol(attr.visibility);
            mermaidCode += `        ${symbol}${attr.type} ${attr.name}\n`;
          });
        }

        // إضافة الـ methods
        if (classInfo.methods && Array.isArray(classInfo.methods)) {
          classInfo.methods.forEach((method: ClassMethod) => {
            const symbol = getVisibilitySymbol(method.visibility);

            // ✅ Handle signature field from backend
            if (method.signature) {
              // Use signature directly from backend
              mermaidCode += `        ${symbol}${method.signature}\n`;
            } else {
              // Fallback to parameters format
              const params = method.parameters
                ?.map((p: MethodParameter) => `${p.name}: ${p.type}`)
                .join(', ') || '';
              const returnType = method.return_type || 'Any';
              mermaidCode += `        ${symbol}${method.name}(${params}) ${returnType}\n`;
            }
          });
        }

        mermaidCode += `    }\n`;
      });
    }

    // إضافة الـ relationships
    if (validRelationships && Array.isArray(validRelationships)) {
      validRelationships.forEach((rel: Relationship) => {
        const fromClass = sanitizeClassName(rel.from);
        const toClass = sanitizeClassName(rel.to);
        const relSyntax = getRelationshipSyntax(rel.type);

        if (rel.label) {
          mermaidCode += `    ${fromClass} ${relSyntax} ${toClass} : ${rel.label}\n`;
        } else {
          mermaidCode += `    ${fromClass} ${relSyntax} ${toClass}\n`;
        }
      });
    }

    return mermaidCode;
  } catch (error) {
    console.error('Error converting JSON to Mermaid:', error);
    throw error;
  }
};

/**
 * استخراج Mermaid code من response
 */
export const extractMermaidCode = (data: any): string => {
  console.log('🔍 Extracting Mermaid code from:', typeof data, data);

  // حالة 1: البيانات بالفعل Mermaid string
  if (typeof data === 'string') {
    if (data.trim().startsWith('classDiagram') || data.trim().startsWith('graph')) {
      console.log('✅ Found direct Mermaid code');
      return data;
    }

    // محاولة parse JSON string
    try {
      const parsed = JSON.parse(data);
      return convertJsonToMermaid(parsed);
    } catch (e) {
      console.warn('⚠️ String is not Mermaid or JSON:', e);
      throw new Error('Invalid diagram data format');
    }
  }

  // حالة 2: object يحتوي على mermaid_code
  if (data && typeof data === 'object') {
    console.log('🔍 Checking object properties:', Object.keys(data));

    if (data.mermaid_code) {
      console.log('✅ Found mermaid_code property');
      if (typeof data.mermaid_code === 'string') {
        return data.mermaid_code;
      }
      return convertJsonToMermaid(data.mermaid_code);
    }

    if (data.diagram) {
      console.log('✅ Found diagram property');
      if (typeof data.diagram === 'string') {
        return data.diagram;
      }
      return convertJsonToMermaid(data.diagram);
    }

    // حالة 3: object يحتوي على classes و relationships
    if (data.classes || data.relationships) {
      console.log('✅ Found JSON structure with classes/relationships');
      console.log('📊 Classes count:', data.classes?.length);
      console.log('📊 Relationships count:', data.relationships?.length);
      return convertJsonToMermaid(data);
    }
  }

  console.error('❌ Unknown diagram data format. Type:', typeof data, 'Keys:', data ? Object.keys(data) : 'null');
  throw new Error('Could not extract Mermaid code from data');
};

export default {
  convertJsonToMermaid,
  extractMermaidCode
};
