SEMANTIC_PROMPT = """
أنت خبير هندسة برمجيات. قارن بين نسختين من الكود وأعطني التناقضات الدلالية فقط.

Class Diagram A:
{diagram_a}

Class Diagram B:
{diagram_b}

أخرج JSON فقط:
{
  "conflicts": [
    {
      "type": "rename | logic_change | breaking_change",
      "severity": "high|medium|low",
      "class_name": "...",
      "member": "...",
      "description": "شرح بالعربي",
      "old_value": "...",
      "new_value": "...",
      "recommendation": "..."
    }
  ]
}
"""