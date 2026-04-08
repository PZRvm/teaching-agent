# Rough Design Skill - Test Scenarios

## RED Phase - Baseline Behavior

### Test Scenario 1: Basic Hand-Drawn Card
**Pressure:** Time pressure + generic AI tendency

**User Request:**
```
Create a hand-drawn style card component with:
- A title
- Description text
- A button
- Hand-drawn aesthetic
```

**Expected Baseline Behavior (WITHOUT skill):**
- AI likely creates standard card with generic styling
- May add rounded corners (not hand-drawn)
- Will probably miss key hand-drawn elements:
  - No rotation/skew
  - No sketch shadows
  - No tape effects
  - No SVG decorations
  - Standard borders instead of thick hand-drawn borders

### Test Scenario 2: Hand-Drawn Form
**Pressure:** Complexity + multiple elements

**User Request:**
```
Create a hand-drawn style login form with:
- Email input
- Password input
- Submit button
- Paper-like background
```

**Expected Baseline Behavior (WITHOUT skill):**
- Standard form layout
- May add some "hand-drawn" class names but wrong implementation
- Missing key hand-drawn elements:
  - No wobbly borders
  - No sketch shadow
  - No tape/paper texture effects
  - No SVG decorative elements

### Test Scenario 3: Hand-Drawn Navigation
**Pressure:** Multiple components + consistency

**User Request:**
```
Create a hand-drawn style navigation bar with:
- Logo
- Navigation links
- User avatar
- Consistent hand-drawn aesthetic with the rest of the page
```

**Expected Baseline Behavior (WITHOUT skill):**
- Standard navbar styling
- Inconsistent with hand-drawn theme
- Missing decorative elements:
  - No hand-drawn underline
  - No tape effects
  - No sketch shadow
  - No rotation on elements

## GREEN Phase - Success Criteria

WITH the rough-design skill, AI should:

### Test Scenario 1: Basic Hand-Drawn Card
✅ Use `border-[3px]` for thick hand-drawn borders
✅ Add `rotate-[-0.5deg]` or similar for slight imperfection
✅ Use `sketch-shadow` class for hard shadow effect
✅ Add tape effect decoration
✅ Include SVG hand-drawn decorative elements

### Test Scenario 2: Hand-Drawn Form
✅ Use wobbly borders with `clip-path`
✅ Add sketch shadow
✅ Use sticky-note colors (sticky-yellow, sticky-blue, etc.)
✅ Include tape/paper texture effects
✅ Add SVG decorations

### Test Scenario 3: Hand-Drawn Navigation
✅ Add hand-drawn underline using SVG path
✅ Use sketch shadow
✅ Include tape effects
✅ Rotate decorative elements slightly
✅ Maintain consistency with hand-drawn theme

## REFACTOR Phase - Common Rationalizations to Address

| Rationalization | Reality | Counter |
|----------------|---------|---------|
| "Just adding rounded corners is enough" | Rounded corners ≠ hand-drawn. Hand-drawn needs imperfection. | Use rotation, skew, thick borders, hard shadows |
| "Hand-drawn is just a style choice" | Hand-drawn is a specific aesthetic with concrete techniques. | Use specific CSS classes and SVG decorations |
| "Too complex for this component" | Hand-drawn works at any complexity level. | Start with basic sketch-shadow and rotation |
| "I'll add decorations later" | Decorations are essential to hand-drawn aesthetic. | Include SVG decorations from the start |
| "Standard borders look fine" | Standard borders look digital, not hand-drawn. | Use thick borders (3px+) with hard shadows |
