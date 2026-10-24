declare module 'mermaid' {
  export interface RenderResult {
    svg: string;
  }

  export interface MermaidConfig {
    startOnLoad?: boolean;
    theme?: string;
    securityLevel?: string;
    fontFamily?: string;
    fontSize?: number;
  }

  export function initialize(config: MermaidConfig): void;
  export function render(id: string, text: string): Promise<RenderResult>;
}

