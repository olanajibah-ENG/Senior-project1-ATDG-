// Utility functions to convert API data to Mermaid syntax

export interface ApiClass {
  name: string;
  attributes: Array<{
    name: string;
    type: string;
    visibility: 'public' | 'private' | 'protected';
  }>;
  methods: Array<{
    name: string;
    parameters?: Array<{
      name: string;
      type: string;
    }>;
    return_type?: string;
    visibility?: 'public' | 'private' | 'protected';
  }>;
  inherits?: string[];
  associations?: Array<{
    type: 'Composition' | 'Aggregation' | 'Association';
    target_class: string;
    attribute?: string;
  }>;
}

export interface ApiDiagramData {
  classes: ApiClass[];
  relationships?: Array<{
    from: string;
    to: string;
    type: 'inheritance' | 'composition' | 'aggregation' | 'association';
    label?: string;
  }>;
}

/**
 * Convert API data to Mermaid diagram syntax
 */
export const generateMermaidFromApi = (data: ApiDiagramData): string => {
  let diagram = "classDiagram\n";
  diagram += "    direction LR\n\n";
  
  // Process classes
  data.classes.forEach(cls => {
    // Class definition
    diagram += `    class ${cls.name} {\n`;
    
    // Add attributes
    cls.attributes.forEach(attr => {
      const visibility = attr.visibility === 'private' ? '-' : 
                        attr.visibility === 'protected' ? '#' : '+';
      diagram += `        ${visibility}${attr.type} ${attr.name}\n`;
    });
    
    // Add methods
    cls.methods.forEach(method => {
      const visibility = method.visibility === 'private' ? '-' : 
                        method.visibility === 'protected' ? '#' : '+';
      
      let methodSignature = `${visibility}${method.name}(`;
      
      if (method.parameters && method.parameters.length > 0) {
        const params = method.parameters.map(p => `${p.name}: ${p.type}`).join(', ');
        methodSignature += params;
      }
      
      methodSignature += ')';
      
      if (method.return_type && method.return_type !== 'void') {
        methodSignature += `: ${method.return_type}`;
      }
      
      diagram += `        ${methodSignature}\n`;
    });
    
    diagram += `    }\n\n`;
  });

  // Add inheritance relationships
  data.classes.forEach(cls => {
    if (cls.inherits && cls.inherits.length > 0) {
      cls.inherits.forEach(parent => {
        if (parent && parent !== null) {
          diagram += `    ${parent} <|-- ${cls.name}\n`;
        }
      });
    }
  });

  // Add associations and compositions
  data.classes.forEach(cls => {
    if (cls.associations && cls.associations.length > 0) {
      cls.associations.forEach(rel => {
        const arrow = rel.type === 'Composition' ? '*--' : 
                     rel.type === 'Aggregation' ? 'o--' : '-->';
        
        const label = rel.attribute ? ` : ${rel.attribute}` : '';
        diagram += `    ${cls.name} ${arrow} ${rel.target_class}${label}\n`;
      });
    }
  });
  
  return diagram;
};

/**
 * Safely parse Python dict string to JSON object
 */
export const parsePythonDictString = (dictString: string): ApiDiagramData => {
  try {
    // Convert Python dict string to valid JSON
    let jsonString = dictString;
    
    // Replace single quotes with double quotes
    jsonString = jsonString.replace(/'/g, '"');
    
    // Replace Python None with null
    jsonString = jsonString.replace(/\bNone\b/g, 'null');
    
    // Replace Python True/False with true/false
    jsonString = jsonString.replace(/\bTrue\b/g, 'true');
    jsonString = jsonString.replace(/\bFalse\b/g, 'false');
    
    // Parse the JSON
    return JSON.parse(jsonString);
  } catch (error) {
    console.error('Error parsing Python dict string:', error);
    throw new Error('Failed to parse API data');
  }
};

/**
 * Process API response data and generate Mermaid code
 */
export const processApiDataToMermaid = (classDiagramData: string | object): string => {
  try {
    let parsedData: ApiDiagramData;
    
    if (typeof classDiagramData === 'string') {
      // Check if it's a Python dict string
      if (classDiagramData.startsWith('{') && classDiagramData.endsWith('}')) {
        parsedData = parsePythonDictString(classDiagramData);
      } else {
        // It's already Mermaid code
        return classDiagramData;
      }
    } else {
      // It's already a parsed object
      parsedData = classDiagramData as ApiDiagramData;
    }
    
    return generateMermaidFromApi(parsedData);
  } catch (error) {
    console.error('Error processing API data:', error);
    throw error;
  }
};
