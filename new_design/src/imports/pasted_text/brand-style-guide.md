---
name: Modern Organic Minimalist
colors:
  surface: '#faf9f5'
  surface-dim: '#dbdad6'
  surface-bright: '#faf9f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f4f0'
  surface-container: '#efeeea'
  surface-container-high: '#e9e8e4'
  surface-container-highest: '#e3e2df'
  on-surface: '#1b1c1a'
  on-surface-variant: '#454835'
  inverse-surface: '#30312e'
  inverse-on-surface: '#f2f1ed'
  outline: '#767963'
  outline-variant: '#c6c9b0'
  surface-tint: '#556500'
  primary: '#556500'
  on-primary: '#ffffff'
  primary-container: '#9ab50a'
  on-primary-container: '#384300'
  inverse-primary: '#b6d332'
  secondary: '#5b623a'
  on-secondary: '#ffffff'
  secondary-container: '#dde4b2'
  on-secondary-container: '#5f663e'
  tertiary: '#5e5e5e'
  on-tertiary: '#ffffff'
  tertiary-container: '#aaaaaa'
  on-tertiary-container: '#3f3f3f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d2f04e'
  primary-fixed-dim: '#b6d332'
  on-primary-fixed: '#181e00'
  on-primary-fixed-variant: '#3f4c00'
  secondary-fixed: '#e0e7b5'
  secondary-fixed-dim: '#c4cb9b'
  on-secondary-fixed: '#191e01'
  on-secondary-fixed-variant: '#444a25'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c6'
  on-tertiary-fixed: '#1b1b1b'
  on-tertiary-fixed-variant: '#474747'
  background: '#faf9f5'
  on-background: '#1b1c1a'
  surface-variant: '#e3e2df'
typography:
  headline-xl:
    fontFamily: newsreader
    fontSize: 64px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: newsreader
    fontSize: 48px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-lg:
    fontFamily: manrope
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  label-md:
    fontFamily: manrope
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin: 32px
---

## Brand & Style

The brand personality is authoritative yet approachable, blending the precision of modern technology with the warmth of organic, paper-like textures. It targets high-level professionals and sophisticated users who value clarity, transparency, and a premium editorial experience.

The design style is a hybrid of **Minimalism** and **Modern Corporate**. It prioritizes heavy whitespace, a restricted but high-impact color palette, and high-quality typography. The goal is to evoke a sense of calm, trustworthiness, and intellectual rigor. Visual interest is generated through purposeful layout and typographic scale rather than decorative elements.

## Colors

The palette is anchored by a warm neutral base that avoids the sterile feel of pure white, creating a "paper" effect. The primary color—a vibrant, acidic lime—serves as a high-visibility accent for calls to action and key highlights.

- **Primary:** Used for primary buttons, active states, and high-priority indicators.
- **Secondary:** A deep, forest-toned neutral used for secondary backgrounds, footers, or text-heavy sections requiring high contrast against the bone-colored background.
- **Tertiary:** Pure black for maximum legibility in body copy and primary headlines.
- **Neutral:** The foundation of the design system, used for global backgrounds and container surfaces.

## Typography

This design system uses a sophisticated typographic pairing to create a high-end editorial feel. 

**Newsreader** is utilized for headlines to convey authority and a classic, literary intelligence. It should be used with tighter tracking in larger sizes.

**Manrope** provides a functional, modern contrast for body text and labels. Its geometric yet friendly proportions ensure readability across complex data and long-form content. Labels should utilize uppercase styling and generous letter spacing to provide clear hierarchy in navigation and metadata.

## Layout & Spacing

The layout follows a **Fixed Grid** model to maintain an editorial, structured appearance. A 12-column grid is standard for desktop views, transitioning to a 4-column grid for mobile.

Spacing is governed by an 8px rhythmic scale. Generous vertical padding (`xl`) is encouraged between major sections to emphasize the minimalist aesthetic and allow content to breathe. Horizontal margins should be substantial, pushing content toward the center to improve readability and focus.

## Elevation & Depth

Depth is achieved through **Tonal Layers** and **Low-Contrast Outlines** rather than traditional shadows. Surfaces are differentiated by slight shifts in color—moving from the neutral base to subtle shades of gray or the secondary dark olive.

When separation is required for interactive elements, use 1px solid borders in a slightly darker shade of the neutral base or the secondary color. Avoid ambient shadows entirely to maintain the "flat paper" aesthetic. Overlays (such as modals) should use a semi-transparent dark backdrop to isolate the content without relying on heavy blur effects.

## Shapes

The shape language is refined and intentional. A moderate roundedness level (`0.5rem`) is the standard for most UI components, such as cards and input fields. 

Larger containers may utilize `rounded-lg` (1rem) to soften the layout, while buttons and small interactive chips may use the `rounded-xl` (1.5rem) or pill-shaped styling to distinguish them clearly from structural containers. This balance ensures the UI feels professional without being overly sharp or clinical.

## Components

### Buttons
Primary buttons use the high-contrast Primary color with black text. Secondary buttons should be ghost-styled with a 1px border or use the Secondary color with white text. Padding should be generous horizontally to create a wide, confident footprint.

### Input Fields
Inputs are minimalist, using a subtle bottom border or a full 1px outline in a muted tone. Focus states transition the border color to the Primary accent. Labels are consistently placed above the input using the `label-lg` typographic style.

### Cards
Cards are flat, defined by 1px borders in a low-contrast color against the background. For elevated importance, cards may use the Secondary background color with light-colored text.

### Chips & Tags
Used for categorization, chips should be small and pill-shaped. They utilize a light tint of the Primary color or a subtle gray to remain unobtrusive but distinct.

### Lists & Navigation
Navigation items are understated, using `label-lg` styling. Active states are indicated by a simple Primary color underline or a small dot, avoiding heavy background highlights.