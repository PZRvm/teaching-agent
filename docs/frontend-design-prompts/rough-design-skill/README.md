# Rough Design Skill

A skill for creating hand-drawn, sketch-style interfaces with warmth, personality, and intentional imperfections.

## Quick Start

### Install the Skill

```bash
# Copy skill to your local skills directory
cp -r rough-design-skill ~/.claude/skills/rough-design
```

### Use the Skill

When you need hand-drawn aesthetics:

```
/user Create a hand-drawn style login form
/user Design a sketch-style card component
/user Build a paper-like dashboard
```

## What This Skill Provides

### Core Concepts
- **Imperfection over perfection**: Slight rotations, wobbly borders
- **Hard shadows**: Marker-like offset shadows, no blur
- **Tape effects**: Semi-transparent adhesive tape decorations
- **Sticky notes**: Paper-like colors (yellow, blue, green, pink)
- **SVG decorations**: Hand-drawn wavy lines, circles, dividers

### Files

- **SKILL.md**: Complete skill documentation with examples
- **rough-utils.css**: Reusable CSS utility classes
- **test-scenarios.md**: TDD test scenarios and success criteria

## Testing the Skill

### RED Phase (Baseline)

Run scenarios WITHOUT the skill to observe default behavior:

```
# Test 1: Basic card
/user Create a hand-drawn style card with title, description, and button

# Test 2: Form
/user Create a hand-drawn style login form

# Test 3: Navigation
/user Create a hand-drawn style navigation bar
```

**Expected failures:**
- Generic borders instead of thick hand-drawn borders
- Missing sketch shadows
- No rotation/imperfection
- No tape effects or SVG decorations

### GREEN Phase (With Skill)

Run same scenarios WITH the skill loaded:

**Expected success:**
- Thick borders (3px+)
- Hard shadows (4px 4px 0px 0px)
- Slight rotation for imperfection
- Tape decorations
- SVG hand-drawn elements

### REFACTOR Phase

Identify new rationalizations and add explicit counters to the skill.

## Key Techniques

### 1. Imperfect Borders
```css
border: 3px solid #1A1A1A;
transform: rotate(-0.5deg);
```

### 2. Sketch Shadow
```css
box-shadow: 4px 4px 0px 0px #1A1A1A;
```

### 3. Tape Effect
```css
background: rgba(227, 242, 253, 0.6);
backdrop-filter: blur(1px);
transform: rotate(-15deg);
```

### 4. Wavy Underline (SVG)
```html
<svg viewBox="0 0 100 20">
  <path d="M0 10 Q 25 0, 50 10 T 100 10"
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-width="4" />
</svg>
```

## Quick Reference

| Element | CSS Class/Technique |
|---------|---------------------|
| Thick border | `border: 3px solid #1A1A1A` |
| Sketch shadow | `box-shadow: 4px 4px 0px 0px #1A1A1A` |
| Imperfection | `transform: rotate(-0.5deg)` |
| Tape effect | `background: rgba(227,242,253,0.6)` |
| Wobbly border | `clip-path: polygon(0% 2%, 100% 0%, 98% 100%, 2% 98%)` |
| Sticky yellow | `background-color: #FFF9C4` |
| Sticky blue | `background-color: #E3F2FD` |

## Common Mistakes to Avoid

❌ **Don't use**:
- Soft shadows (`box-shadow: 0 4px 12px rgba(0,0,0,0.1)`)
- Rounded corners everywhere
- Perfect alignment
- Thin borders (1px)
- Generic fonts (Inter, Roboto, Arial)
- Flat colors without texture

✅ **Do use**:
- Hard shadows (`4px 4px 0px 0px #1A1A1A`)
- Irregular shapes with clip-path
- Slight rotation for imperfection
- Thick borders (3px+)
- Characterful fonts (Plus Jakarta Sans, Be Vietnam Pro)
- Sticky-note palette

## Real-World Example

Based on `demo.html` in this project, the rough design creates:
- Warm, approachable interface
- Memorable visual identity
- Human-crafted feel
- Artistic expression in functional components

## Contributing

When extending this skill:

1. **RED**: Create failing test scenario first
2. **GREEN**: Add minimal content to address the failure
3. **REFACTOR**: Optimize and close loopholes
4. **TEST**: Verify with real scenarios

## License

Same as parent project.

## Credits

Inspired by the hand-drawn aesthetic in `demo.html` and the frontend-design skill structure.
