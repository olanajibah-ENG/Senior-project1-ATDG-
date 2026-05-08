// Professional UML Diagram Themes and Styling Configuration
// فصل تنسيق المخطط في ملف منفصل لسهولة الصيانة والتخصيص

export interface DiagramTheme {
  name: string;
  description: string;
  direction: 'TB' | 'LR' | 'BT' | 'RL';
  mermaidConfig: any;
  cssFile: string; // Path to the CSS file
  additionalClasses?: string[]; // Additional CSS classes to apply
  layoutConfig: {
    nodeSpacing: number;
    rankSpacing: number;
    diagramPadding: number;
  };
  exportSettings?: {
    excludePatterns?: string[]; // Patterns to exclude from export
    includeOnlyPatterns?: string[]; // Only include classes matching these patterns
    excludeUnknownClasses?: boolean; // Exclude classes with 'Unknown' in name
    excludeDefaultClasses?: boolean; // Exclude classes with 'defaultClass' in name
  };
}

// ألوان UML المهنية
export const UML_COLORS = {
  primary: '#ffffff',      // أبيض للخلفيات
  secondary: '#f8f9fa',    // رمادي فاتح
  accent: '#e9ecef',       // رمادي أفتح
  background: '#ffffff',   // خلفية بيضاء
  text: '#000000',         // نص أسود
  border: '#000000',       // حدود سوداء
  relationship: '#000000', // خطوط العلاقات
  inheritance: '#059669',  // أخضر للوراثة
  composition: '#dc2626',  // أحمر للتملك
  aggregation: '#ea580c',  // برتقالي للتجميع
  association: '#2563eb',  // أزرق للارتباط
};

// تنسيقات المخطط المختلفة
export const DIAGRAM_THEMES: Record<string, DiagramTheme> = {
  // المخطط الأفقي الكلاسيكي (الافتراضي)
  horizontal: {
    name: 'أفقي كلاسيكي',
    description: 'مخطط أفقي واضح مع حدود سوداء وخطوط نظيفة',
    direction: 'LR',
    layoutConfig: {
      nodeSpacing: 120,
      rankSpacing: 100,
      diagramPadding: 30
    },
    mermaidConfig: {
      startOnLoad: false,
      theme: 'default',
      fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
      securityLevel: 'loose'
    },
    cssFile: './styles/diagram.css',
    additionalClasses: [],
    exportSettings: {
      excludePatterns: ['defaultClass', 'Unknown', 'unknown'],
      excludeUnknownClasses: true,
      excludeDefaultClasses: true
    }
  },

  // المخطط الأفقي مع شبكة
  horizontalWithGrid: {
    name: 'أفقي مع شبكة',
    description: 'مخطط أفقي مع خطوط شبكة للمساعدة في القراءة',
    direction: 'LR',
    layoutConfig: {
      nodeSpacing: 120,
      rankSpacing: 100,
      diagramPadding: 30
    },
    mermaidConfig: {
      startOnLoad: false,
      theme: 'default',
      fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
      securityLevel: 'loose'
    },
    cssFile: './styles/diagram.css',
    additionalClasses: ['grid-bg'],
    exportSettings: {
      excludePatterns: ['defaultClass', 'Unknown', 'unknown'],
      excludeUnknownClasses: true,
      excludeDefaultClasses: true
    }
  },

  // المخطط الرأسي المهني
  vertical: {
    name: 'رأسي مهني',
    description: 'مخطط رأسي احترافي يتبع معايير UML',
    direction: 'TB',
    layoutConfig: {
      nodeSpacing: 120,
      rankSpacing: 100,
      diagramPadding: 30
    },
    mermaidConfig: {
      startOnLoad: false,
      theme: 'default',
      fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
      securityLevel: 'loose'
    },
    cssFile: './styles/diagram.css',
    additionalClasses: [],
    exportSettings: {
      excludePatterns: ['defaultClass', 'Unknown', 'unknown'],
      excludeUnknownClasses: true,
      excludeDefaultClasses: true
    }
  }
};

// دالة للحصول على الثيم الافتراضي
export function getDefaultTheme(): DiagramTheme {
  return DIAGRAM_THEMES.horizontal;
}

// دالة للحصول على ثيم محدد
export function getTheme(themeName: string): DiagramTheme {
  return DIAGRAM_THEMES[themeName] || getDefaultTheme();
}

// دالة للحصول على أسماء جميع الثيمات المتاحة
export function getAvailableThemes(): string[] {
  return Object.keys(DIAGRAM_THEMES);
}

// دالة لتخصيص إعدادات التصدير للثيم
export function customizeThemeExportSettings(
  themeName: string,
  exportSettings: DiagramTheme['exportSettings']
): DiagramTheme {
  const theme = getTheme(themeName);
  return {
    ...theme,
    exportSettings: {
      ...theme.exportSettings,
      ...exportSettings
    }
  };
}

// دالة للحصول على إعدادات التصدير الحالية
export function getThemeExportSettings(themeName: string): DiagramTheme['exportSettings'] {
  const theme = getTheme(themeName);
  return theme.exportSettings || {};
}

// دالة لإنشاء كود Mermaid مع تطبيق الثيم
export const generateMermaidCodeWithTheme = (
  classes: any[],
  relationships: any[],
  theme: DiagramTheme,
  title?: string
): string => {
  let mermaidCode = 'classDiagram\n';

  if (title) {
    mermaidCode += `    title ${title}\n`;
  }

  mermaidCode += '    direction LR\n\n';

  // Filter out unwanted classes based on theme export settings
  const exportSettings = theme.exportSettings || {};
  const excludePatterns = exportSettings.excludePatterns || [];
  const excludeUnknown = exportSettings.excludeUnknownClasses !== false; // default to true
  const excludeDefault = exportSettings.excludeDefaultClasses !== false; // default to true

  const filteredClasses = classes.filter(cls => {
    const className = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
    const originalClassName = cls.name.trim();
    
    // Check if class should be excluded based on patterns
    const shouldExcludeByPattern = excludePatterns.some(pattern => 
      className.toLowerCase().includes(pattern.toLowerCase()) ||
      originalClassName.toLowerCase().includes(pattern.toLowerCase())
    );
    
    // Check for unknown classes
    const isUnknown = excludeUnknown && (
      className.toLowerCase().includes('unknown') || 
      originalClassName.toLowerCase().includes('unknown')
    );
    
    // Check for default classes
    const isDefault = excludeDefault && (
      className.toLowerCase().includes('defaultclass') || 
      originalClassName.toLowerCase().includes('defaultclass')
    );
    
    // Check for numeric-only class names
    const isNumericOnly = /^\d+$/.test(className);
    
    // Check for empty class names
    const isEmpty = originalClassName === '';
    
    return !shouldExcludeByPattern && !isUnknown && !isDefault && !isNumericOnly && !isEmpty;
  });

  console.log('🔍 Original classes:', classes.length);
  console.log('🔍 Original class names:', classes.map(c => c.name));
  console.log('🔍 Filtered classes:', filteredClasses.length);
  console.log('🔍 Filtered class names:', filteredClasses.map(c => c.name));
  console.log('🔍 Filtered out classes:', classes.map(c => c.name).filter(name => 
    name.includes('defaultClass') || name.includes('Unknown') || name.includes('unknown')
  ));

  // Filter relationships to remove those involving filtered classes
  const filteredRelationships = relationships.filter(rel => {
    const fromExists = filteredClasses.some(cls => cls.name === rel.from);
    const toExists = filteredClasses.some(cls => cls.name === rel.to);
    // Also filter out relationships with 'Unknown' targets
    const noUnknown = !rel.to.includes('Unknown') && !rel.to.includes('unknown') && !rel.from.includes('Unknown') && !rel.from.includes('unknown');
    return fromExists && toExists && noUnknown;
  });

  console.log('🔍 Original relationships:', relationships.length);
  console.log('🔍 Filtered relationships:', filteredRelationships.length);

  // إضافة الكلاسات
  filteredClasses.forEach(cls => {
    const className = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
    mermaidCode += `    class ${className}{\n`;

    // إضافة الخصائص
    if (cls.attributes && cls.attributes.length > 0) {
      cls.attributes.forEach((attr: any) => {
        let cleanAttr = '';
        if (typeof attr === 'string') {
          cleanAttr = attr.trim();
        } else if (typeof attr === 'object' && attr.name) {
          // Handle object format: {name: 'attrName', type: 'String', visibility: 'protected'}
          const visibility = attr.visibility || 'private';
          const visibilitySymbol = visibility === 'public' ? '+' : 
                                  visibility === 'protected' ? '#' : 
                                  visibility === 'package' ? '~' : '-';
          cleanAttr = `${visibilitySymbol} ${attr.name}${attr.type ? ': ' + attr.type : ''}`;
        } else {
          cleanAttr = String(attr).trim();
        }
        
        // Convert any visibility indicators to UML symbols
        cleanAttr = cleanAttr.replace(/^\+/, '+').replace(/^-/, '-').replace(/^#/, '#').replace(/^~/, '~');
        // Ensure visibility symbol exists, default to private if none
        if (!cleanAttr.match(/^[\+\-\#~]/)) {
          cleanAttr = `- ${cleanAttr}`;
        }
        mermaidCode += `        ${cleanAttr}\n`;
      });
    }

    // إضافة الفاصل
    if (cls.attributes?.length > 0 && cls.methods?.length > 0) {
      mermaidCode += '        --\n';
    }

    // إضافة الأساليب
    if (cls.methods && cls.methods.length > 0) {
      cls.methods.forEach((method: string) => {
        let cleanMethod = method.trim();
        // Convert any visibility indicators to UML symbols
        cleanMethod = cleanMethod.replace(/^\+/, '+').replace(/^-/, '-').replace(/^#/, '#').replace(/^~/, '~');
        // Ensure visibility symbol exists, default to public if none
        if (!cleanMethod.match(/^[\+\-\#~]/)) {
          cleanMethod = `+ ${cleanMethod}`;
        }
        mermaidCode += `        ${cleanMethod}\n`;
      });
    }

    mermaidCode += '    }\n\n';
  });

  // إضافة العلاقات
  filteredRelationships.forEach(rel => {
    let arrow = '';
    const fromClass = rel.from.replace(/[^a-zA-Z0-9_]/g, '_');
    const toClass = rel.to.replace(/[^a-zA-Z0-9_]/g, '_');

    switch (rel.type) {
      case 'inheritance':
        arrow = '<|--';
        break;
      case 'implementation':
        arrow = '<|..';
        break;
      case 'composition':
        arrow = '*--';
        break;
      case 'aggregation':
        arrow = 'o--';
        break;
      case 'association':
        arrow = '-->';
        break;
      default:
        arrow = '-->';
    }

    mermaidCode += `    ${fromClass} ${arrow} ${toClass}`;
    if (rel.label) {
      mermaidCode += ` : ${rel.label}`;
    }
    mermaidCode += '\n';
  });

  // إضافة التنسيقات حسب الثيم
  mermaidCode += '\n    %% Professional UML Styling\n';
  mermaidCode += `    classDef defaultClass fill:#ffffff,stroke:#2563eb,stroke-width:2px,color:#1f2937\n`;
  mermaidCode += `    classDef interfaceClass fill:#e0f2fe,stroke:#1e40af,stroke-width:2px,color:#1e293b\n`;
  mermaidCode += `    classDef abstractClass fill:#fef3c7,stroke:#ea580c,stroke-width:2px,color:#92400e\n`;

  // تطبيق التنسيقات على الكلاسات
  filteredClasses.forEach(cls => {
    const className = cls.name.replace(/[^a-zA-Z0-9_]/g, '_');
    if (cls.isAbstract) {
      if (cls.name.toLowerCase().includes('interface')) {
        mermaidCode += `    class ${className} interfaceClass\n`;
      } else {
        mermaidCode += `    class ${className} abstractClass\n`;
      }
    } else {
      mermaidCode += `    class ${className} defaultClass\n`;
    }
  });

  return mermaidCode;
}
