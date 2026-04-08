# Rough Design Skill - Creation Summary

## Overview

A complete skill for creating hand-drawn, sketch-style interfaces with warmth, personality, and intentional imperfections. Created following TDD discipline.

## Files Created

```
rough-design-skill/
├── SKILL.md              # Main skill documentation
├── rough-utils.css       # Reusable CSS utility classes
├── examples.html         # Complete working examples
├── test-scenarios.md     # TDD test scenarios
├── README.md            # Quick start guide
└── CREATION_SUMMARY.md  # This file
```

## TDD Process Followed

### ✅ RED Phase
- Created test scenarios to identify baseline behavior
- Documented expected failures without the skill
- Identified patterns in generic AI responses

### ✅ GREEN Phase
- Wrote minimal skill addressing specific failures
- Included concrete techniques and examples
- Added rationalization counters

### ✅ REFACTOR Phase
- Removed Tailwind CSS dependencies (per user request)
- Added pure CSS and styled-components implementations
- Included complete working examples

## Key Techniques Documented

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

### 4. SVG Decorations
```html
<svg viewBox="0 0 100 20">
  <path d="M0 10 Q 25 0, 50 10 T 100 10"
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-width="4" />
</svg>
```

## Color Palette

```css
--sticky-yellow: #FFF9C4;
--sticky-blue: #E3F2FD;
--sticky-green: #E8F5E9;
--sticky-pink: #FCE4EC;
```

## Common Mistakes Addressed

| Mistake | Fix |
|---------|-----|
| Soft shadows | Hard shadows: `4px 4px 0px 0px #1A1A1A` |
| Perfect alignment | Slight rotation: `rotate(-0.5deg)` |
| Thin borders | Thick borders: `3px` or more |
| Generic fonts | Characterful fonts: Plus Jakarta Sans, Be Vietnam Pro |
| Missing decorations | Always add SVG decorations or tape effects |

## Installation

```bash
# Copy to local skills directory
cp -r rough-design-skill ~/.claude/skills/rough-design
```

## Usage Examples

### Styled Components (React)
```tsx
const Wrapper = styled.div`
  border: 3px solid #1A1A1A;
  box-shadow: 4px 4px 0px 0px #1A1A1A;
  background: #E3F2FD;
  padding: 40px;
  transform: rotate(-0.5deg);
`
```

### Plain CSS
```css
.rough-card {
  border: 3px solid #1A1A1A;
  box-shadow: 4px 4px 0px 0px #1A1A1A;
  background: #E3F2FD;
  padding: 40px;
  transform: rotate(-0.5deg);
}
```

## Testing

To test the skill:

1. **Without skill**: Observe generic responses
2. **With skill**: Verify hand-drawn techniques applied
3. **Refine**: Address new rationalizations

## Success Criteria

✅ Thick borders (3px+)
✅ Hard shadows (no blur)
✅ Slight rotation for imperfection
✅ Tape decorations
✅ SVG hand-drawn elements
✅ Characterful fonts
✅ Sticky-note palette
✅ No Tailwind CSS dependencies

## Real-World Application

Based on `demo.html` from the project, this skill creates:
- Warm, approachable interfaces
- Memorable visual identity
- Human-crafted feel
- Artistic expression in functional components

## Next Steps

1. **Install**: Add to local skills directory
2. **Test**: Run test scenarios to verify
3. **Use**: Apply to real projects
4. **Refine**: Update based on usage patterns

## Contributing

When extending this skill:
1. Follow TDD: RED → GREEN → REFACTOR
2. Test with real scenarios
3. Document rationalizations
4. Keep examples current

## License

Same as parent project.

## Credits

- Based on `demo.html` hand-drawn aesthetic
- Structure inspired by `frontend-design` skill
- Created following TDD discipline from `superpowers:writing-skills`
