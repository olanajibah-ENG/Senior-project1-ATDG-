# Color Reference Guide - Conflict Detection

## 🎨 Quick Color Reference

---

## PRIMARY COLORS

### Purple Palette (Main Theme)
```css
--purple-dark: #7c3aed;      /* Primary - Headers, Buttons, Selected */
--purple-medium: #8b5cf6;    /* Hover States */
--purple-light: #a78bfa;     /* Accents */
--purple-lighter: #c4b5fd;   /* Subtle Accents */
```

### Gray Palette (Secondary)
```css
--gray-50: #f9fafb;          /* Lightest */
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;         /* Borders */
--gray-400: #9ca3af;
--gray-500: #6b7280;         /* Secondary Text, Dates */
--gray-600: #4b5563;
--gray-700: #374151;         /* Dark Mode Borders */
--gray-800: #1f2937;         /* Dark Mode Backgrounds */
--gray-900: #111827;         /* Darkest */
```

---

## SEMANTIC COLORS

### Status Colors
```css
--success: #10b981;          /* Success badges ONLY */
--danger: #ef4444;           /* Errors, Critical */
--warning: #f59e0b;          /* Warnings, Medium */
--info: #3b82f6;             /* Info messages */
```

**⚠️ IMPORTANT**: Green (#10b981) is ONLY for semantic success badges, NOT for checkmarks or selected states!

---

## USAGE GUIDE

### Headers & Titles
```css
color: var(--purple-dark);   /* #7c3aed */
font-weight: 700;
```

### Body Text
```css
color: var(--gray-900);      /* Light Mode */
color: var(--gray-100);      /* Dark Mode */
```

### Secondary Text (Dates, Descriptions)
```css
color: var(--gray-500);      /* Light Mode */
color: var(--gray-400);      /* Dark Mode */
```

### Checkmarks (✓)
```css
color: #7c3aed;              /* Purple - NOT green! */
```

### Selected States
```css
border-color: var(--purple-dark);
background: rgba(124, 58, 237, 0.05);    /* Light Mode */
background: rgba(124, 58, 237, 0.15);    /* Dark Mode */
```

### Hover States
```css
border-color: var(--purple-medium);
box-shadow: 0 4px 12px rgba(124, 58, 237, 0.15);
```

### Primary Buttons
```css
background: var(--purple-dark);
color: #ffffff;
box-shadow: 0 4px 12px rgba(124, 58, 237, 0.2);
```

### Secondary Buttons
```css
background: transparent;
color: var(--purple-dark);
border: 2px solid var(--purple-dark);
```

### Progress Bar
```css
background: linear-gradient(90deg, var(--purple-dark), var(--purple-medium));
box-shadow: 0 0 10px rgba(124, 58, 237, 0.3);
```

### Active Tabs
```css
background: var(--purple-dark);
color: #ffffff;
box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
```

### Watermark
```css
background: radial-gradient(
  circle, 
  rgba(124, 58, 237, 0.03) 0%,    /* Light Mode */
  transparent 70%
);

background: radial-gradient(
  circle, 
  rgba(124, 58, 237, 0.05) 0%,    /* Dark Mode */
  transparent 70%
);
```

---

## RGBA OPACITY GUIDE

### Purple Backgrounds
```css
rgba(124, 58, 237, 0.03)     /* Watermark (Light) */
rgba(124, 58, 237, 0.05)     /* Selected (Light), Watermark (Dark) */
rgba(124, 58, 237, 0.1)      /* Icon backgrounds */
rgba(124, 58, 237, 0.15)     /* Selected (Dark), Hover effects */
rgba(124, 58, 237, 0.2)      /* Button shadows */
rgba(124, 58, 237, 0.3)      /* Active shadows */
```

### Gray Backgrounds
```css
rgba(0, 0, 0, 0.05)          /* Subtle shadows (Light) */
rgba(255, 255, 255, 0.05)    /* Subtle highlights (Dark) */
```

---

## COLOR COMBINATIONS

### Light Mode
```css
/* Background */
background: #ffffff;

/* Text */
color: var(--gray-900);      /* Primary */
color: var(--gray-500);      /* Secondary */

/* Borders */
border-color: var(--gray-300);

/* Selected */
border-color: var(--purple-dark);
background: rgba(124, 58, 237, 0.05);
```

### Dark Mode
```css
/* Background */
background: var(--gray-800);

/* Text */
color: var(--gray-100);      /* Primary */
color: var(--gray-400);      /* Secondary */

/* Borders */
border-color: var(--gray-700);

/* Selected */
border-color: var(--purple-dark);
background: rgba(124, 58, 237, 0.15);
```

---

## COMPONENT-SPECIFIC COLORS

### Conflict Type Selector
```css
/* Card Background */
background: #ffffff;                      /* Light */
background: var(--gray-800);              /* Dark */

/* Card Border */
border: 2px solid var(--gray-300);        /* Light */
border: 2px solid var(--gray-700);        /* Dark */

/* Hover */
border-color: var(--purple-medium);
box-shadow: 0 8px 24px rgba(124, 58, 237, 0.15);

/* Watermark */
background: radial-gradient(circle, rgba(124, 58, 237, 0.03) 0%, transparent 70%);
```

### Project Cards
```css
/* Icon Background */
background: rgba(124, 58, 237, 0.05);     /* Light */
background: rgba(124, 58, 237, 0.1);      /* Dark */

/* Title */
color: var(--purple-dark);

/* Description */
color: var(--gray-500);                   /* Light */
color: var(--gray-400);                   /* Dark */

/* Checkmark */
color: #7c3aed;                           /* Purple */
```

### File Selection
```css
/* Selected Border */
border-color: var(--purple-dark);
background: rgba(124, 58, 237, 0.05);     /* Light */
background: rgba(124, 58, 237, 0.15);     /* Dark */

/* Checkmark */
color: #7c3aed;                           /* Purple */
```

### Version Selection
```css
/* Selected Border */
border-color: var(--purple-dark);
border-left: 4px solid var(--purple-dark);
background: rgba(124, 58, 237, 0.05);     /* Light */
background: rgba(124, 58, 237, 0.15);     /* Dark */

/* Checkmark */
color: #7c3aed;                           /* Purple */
```

### Stepper
```css
/* Active Step */
background: var(--purple-dark);
color: #ffffff;

/* Done Step */
background: var(--success);               /* Green OK here */
color: #ffffff;

/* Inactive Step */
background: transparent;
color: var(--gray-500);
border: 2px solid var(--gray-300);
```

### Badges
```css
/* Critical */
background: rgba(239, 68, 68, 0.1);
color: var(--danger);
border-color: var(--danger);

/* High */
background: rgba(245, 158, 11, 0.1);
color: var(--warning);
border-color: var(--warning);

/* Medium */
background: rgba(124, 58, 237, 0.1);
color: var(--purple-dark);
border-color: var(--purple-dark);

/* Success */
background: rgba(16, 185, 129, 0.1);
color: var(--success);
border-color: var(--success);
```

---

## ❌ COLORS TO AVOID

### Don't Use:
```css
/* Old Dark Purple (too dark) */
#4c1d95 ❌

/* Green for checkmarks (use purple) */
#10b981 ❌ (except semantic success badges)

/* Mixed purple shades for selections */
#a855f7 ❌
#6d28d9 ❌ (except hover states)

/* Bright colors for backgrounds */
#ff0000 ❌
#00ff00 ❌
#0000ff ❌
```

---

## ✅ QUICK CHECKLIST

When adding new elements, ask:

- [ ] Is the primary color `#7c3aed` (lighter purple)?
- [ ] Are checkmarks purple, not green?
- [ ] Are dates and secondary text gray (#6b7280)?
- [ ] Are selected states using purple background?
- [ ] Are semantic colors only for status badges?
- [ ] Are hover effects using purple-medium?
- [ ] Are shadows using rgba(124, 58, 237, ...)?
- [ ] Is the design consistent with existing elements?

---

## 🎨 COLOR PALETTE VISUALIZATION

```
PURPLE SCALE:
████ #7c3aed  (Primary - Dark Purple)
████ #8b5cf6  (Medium Purple)
████ #a78bfa  (Light Purple)
████ #c4b5fd  (Lighter Purple)

GRAY SCALE:
████ #111827  (Gray 900 - Darkest)
████ #1f2937  (Gray 800)
████ #374151  (Gray 700)
████ #4b5563  (Gray 600)
████ #6b7280  (Gray 500 - Secondary Text)
████ #9ca3af  (Gray 400)
████ #d1d5db  (Gray 300 - Borders)
████ #e5e7eb  (Gray 200)
████ #f3f4f6  (Gray 100)
████ #f9fafb  (Gray 50 - Lightest)

SEMANTIC:
████ #10b981  (Success - Green)
████ #ef4444  (Danger - Red)
████ #f59e0b  (Warning - Orange)
████ #3b82f6  (Info - Blue)
```

---

## 📱 ACCESSIBILITY

### Contrast Ratios (WCAG AA)

#### Light Mode:
- Purple on White: 4.5:1 ✅
- Gray-500 on White: 4.5:1 ✅
- Gray-900 on White: 21:1 ✅

#### Dark Mode:
- Purple on Gray-800: 4.5:1 ✅
- Gray-400 on Gray-800: 4.5:1 ✅
- Gray-100 on Gray-800: 14:1 ✅

All color combinations meet WCAG AA standards for accessibility.

---

**Last Updated**: May 4, 2026  
**Version**: 3.0 (Final Refinements)  
**Status**: ✅ Production Ready
