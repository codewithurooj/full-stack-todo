# UI Specification: Shared Components & Layout

**Feature**: Shared UI Components and Application Layout
**Created**: 2025-12-12
**Status**: Draft
**Related Specs**:
- `specs/features/001-task-crud/spec.md`
- `specs/features/002-authentication/spec.md`
- `specs/ui/authentication-ui.md`

## Overview

This specification defines all reusable UI components, layout structures, and design system elements used throughout the todo application. These components provide consistency, maintainability, and a cohesive user experience across all features.

## Application Layout

### AppLayout Component

**Purpose**: Provide the main application structure with header, content area, and optional footer.

**Layout Structure**:
```
┌─────────────────────────────────────┐
│           Header                    │
├─────────────────────────────────────┤
│                                     │
│         Main Content Area           │
│         (children rendered here)    │
│                                     │
├─────────────────────────────────────┤
│           Footer (optional)         │
└─────────────────────────────────────┘
```

**Usage**:
```typescript
<AppLayout>
  <DashboardPage />
</AppLayout>
```

**Props**:
```typescript
interface AppLayoutProps {
  children: React.ReactNode;
  showHeader?: boolean; // Default: true
  showFooter?: boolean; // Default: false
}
```

**Visual Specifications**:
- Header: Fixed at top, full width, height 64px
- Main content: Flexible height, max-width 1200px, centered
- Footer: Sticky at bottom when content is short
- Background: Light neutral color
- Responsive padding

**Acceptance Criteria**:
1. **Given** I am viewing any page with layout, **When** I scroll down, **Then** the header remains fixed at the top
2. **Given** I am on a page with minimal content, **When** I view the page, **Then** the footer sticks to the bottom of the viewport
3. **Given** I resize my browser, **When** the viewport changes, **Then** the layout adjusts responsively without breaking

---

### Header Component

**Purpose**: Display app branding, navigation, and user controls at the top of every page.

**Visual Elements**:
- App logo/name on the left
- Navigation links in center (if applicable)
- User profile menu on the right
- Sign out button (via profile menu)
- Border bottom for visual separation

**Props**:
```typescript
interface HeaderProps {
  user?: User | null;
  onSignOut?: () => void;
  showNav?: boolean; // Default: true
}
```

**Layout Specifications**:
- Height: 64px (4rem)
- Horizontal padding: 24px (1.5rem)
- Flexbox layout: space-between alignment
- Background: White or brand color
- Border bottom: 1px solid light grey
- Z-index: 1000 (above other content)

**Responsive Behavior**:
- Mobile (< 768px): Hide text labels, show icons only
- Desktop: Show full text labels and logo

**Acceptance Criteria**:
1. **Given** I am signed in, **When** I view the header, **Then** I see the app logo and my profile menu
2. **Given** I am not signed in, **When** I view authentication pages, **Then** the header shows only the app logo
3. **Given** I am on mobile, **When** I view the header, **Then** it adapts to smaller screen size appropriately

---

### Footer Component (Optional)

**Purpose**: Provide copyright information, links, and additional navigation at the bottom of pages.

**Visual Elements**:
- Copyright text
- Links (Privacy Policy, Terms of Service, Help)
- Social media icons (optional)
- Subtle styling to not distract from main content

**Props**:
```typescript
interface FooterProps {
  showLinks?: boolean; // Default: true
  variant?: 'minimal' | 'full'; // Default: 'minimal'
}
```

**Layout Specifications**:
- Height: auto (min 80px)
- Horizontal padding: 24px
- Background: Light grey
- Text: Small, grey color
- Center-aligned content

**Acceptance Criteria**:
1. **Given** I am viewing a page with footer, **When** I scroll to the bottom, **Then** I see copyright and links
2. **Given** I click a footer link, **When** the link is clicked, **Then** I navigate to the appropriate page

---

## Form Components

### Input Component

**Purpose**: Reusable text input field with labels, validation, and error states.

**Variants**:
- Text input
- Email input
- Password input (with show/hide toggle)
- Textarea (multiline)
- Number input

**Props**:
```typescript
interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'textarea';
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  placeholder?: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  maxLength?: number;
  rows?: number; // For textarea
  autoFocus?: boolean;
  name?: string;
  id?: string;
}
```

**Visual States**:
1. **Default**: Normal border, label above field
2. **Focus**: Highlighted border (primary color), focus ring
3. **Error**: Red border, error message below in red
4. **Disabled**: Greyed out, cursor not-allowed
5. **Success**: Green border (optional, for confirmed valid input)

**Visual Specifications**:
- Height: 40px (44px for mobile touch targets)
- Padding: 12px horizontal, 8px vertical
- Border: 1px solid grey (#D1D5DB)
- Border radius: 6px
- Font size: 16px (prevents zoom on mobile)
- Label: 14px, medium weight, 4px margin bottom
- Error text: 14px, red color (#DC2626)
- Helper text: 14px, grey color

**Password Input Specifics**:
- Show/hide icon button on right
- Icon toggles between eye (show) and eye-slash (hide)
- Maintains focus when toggling visibility

**Accessibility**:
- Label associated with input via `for` attribute
- Error message has `role="alert"` and is aria-live
- Required fields indicated with `*` and `aria-required`
- Helper text linked via `aria-describedby`

**Acceptance Criteria**:
1. **Given** I focus on an input, **When** the input receives focus, **Then** I see a visible focus ring and border highlight
2. **Given** an input has an error, **When** the error state is set, **Then** I see a red border and error message below the field
3. **Given** a password input, **When** I click the show/hide toggle, **Then** the password visibility changes
4. **Given** I am using keyboard, **When** I tab through inputs, **Then** they receive focus in logical order
5. **Given** an input is disabled, **When** I try to interact, **Then** I cannot edit or focus the field

---

### Button Component

**Purpose**: Reusable button for all user actions with consistent styling and states.

**Variants**:
- **Primary**: Solid background, main actions (submit, save, create)
- **Secondary**: Outlined, secondary actions (cancel, back)
- **Danger**: Red color, destructive actions (delete, remove)
- **Ghost**: Transparent background, subtle actions
- **Link**: Text-only, appears as hyperlink

**Sizes**:
- Small: 32px height
- Medium: 40px height (default)
- Large: 48px height

**Props**:
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'link';
  size?: 'small' | 'medium' | 'large';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}
```

**Visual Specifications**:

**Primary Button**:
- Background: Brand primary color
- Text: White
- Hover: Slightly darker background
- Active: Even darker, slight scale down
- Disabled: 50% opacity, cursor not-allowed

**Secondary Button**:
- Background: Transparent
- Border: 1px solid primary color
- Text: Primary color
- Hover: Light primary background
- Active: Slightly darker background

**Danger Button**:
- Background: Red (#DC2626)
- Text: White
- Hover: Darker red
- Active: Even darker red

**Loading State**:
- Shows spinner icon
- Disabled during loading
- Text may change (e.g., "Saving...")
- Maintains button dimensions

**Sizing**:
```css
Small:  padding: 6px 12px, font: 14px
Medium: padding: 10px 20px, font: 16px
Large:  padding: 12px 24px, font: 18px
```

**Accessibility**:
- Adequate touch target (min 44x44px on mobile)
- Focus visible indicator
- Disabled state announced to screen readers
- Loading state announced with aria-live

**Acceptance Criteria**:
1. **Given** a button is loading, **When** loading state is active, **Then** I see a spinner and the button is disabled
2. **Given** I hover over a button, **When** my cursor is over it, **Then** I see hover state styling
3. **Given** a button is disabled, **When** I try to click, **Then** no action occurs
4. **Given** I focus a button with keyboard, **When** it has focus, **Then** I see a clear focus indicator
5. **Given** different button variants, **When** displayed together, **Then** they maintain visual hierarchy (primary > secondary > ghost)

---

### Checkbox Component

**Purpose**: Allow users to select binary options (checked/unchecked).

**Props**:
```typescript
interface CheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  indeterminate?: boolean; // For "partially selected" state
  name?: string;
  id?: string;
}
```

**Visual Specifications**:
- Size: 20px × 20px
- Border: 2px solid grey
- Border radius: 4px
- Checked: Primary color background with white checkmark
- Hover: Slight border color change
- Focus: Focus ring around checkbox

**States**:
1. Unchecked: Empty box with border
2. Checked: Filled with checkmark
3. Indeterminate: Filled with dash (for "select all" scenarios)
4. Disabled: Greyed out, 50% opacity

**Accessibility**:
- Native checkbox element styled
- Label associated properly
- Keyboard accessible (Space to toggle)
- Focus visible

**Acceptance Criteria**:
1. **Given** I click a checkbox, **When** clicked, **Then** it toggles between checked and unchecked
2. **Given** I use keyboard, **When** I press Space on focused checkbox, **Then** it toggles state
3. **Given** a checkbox is disabled, **When** I try to interact, **Then** it does not change state

---

## Feedback Components

### Alert Component

**Purpose**: Display important messages to users (success, error, warning, info).

**Variants**:
- **Success**: Green - confirms successful actions
- **Error**: Red - indicates errors or problems
- **Warning**: Yellow/Orange - warns about potential issues
- **Info**: Blue - provides helpful information

**Props**:
```typescript
interface AlertProps {
  variant: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  onClose?: () => void;
  dismissible?: boolean;
  icon?: boolean; // Show icon, default: true
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

**Visual Specifications**:
- Padding: 16px
- Border radius: 8px
- Border: 1px solid (slightly darker than background)
- Icon on left (20px × 20px)
- Close button on right (if dismissible)
- Title: Bold, 16px
- Message: Regular, 14px

**Color Schemes**:
```
Success:
  - Background: #ECFDF5 (light green)
  - Border: #10B981 (green)
  - Text: #065F46 (dark green)
  - Icon: #10B981

Error:
  - Background: #FEF2F2 (light red)
  - Border: #DC2626 (red)
  - Text: #991B1B (dark red)
  - Icon: #DC2626

Warning:
  - Background: #FFFBEB (light yellow)
  - Border: #F59E0B (orange)
  - Text: #92400E (dark orange)
  - Icon: #F59E0B

Info:
  - Background: #EFF6FF (light blue)
  - Border: #3B82F6 (blue)
  - Text: #1E40AF (dark blue)
  - Icon: #3B82F6
```

**Accessibility**:
- `role="alert"` for error/warning
- `role="status"` for success/info
- Adequate color contrast
- Icon is decorative (aria-hidden)
- Screen reader announces message

**Acceptance Criteria**:
1. **Given** an alert is displayed, **When** I view it, **Then** I can clearly identify its type by color and icon
2. **Given** a dismissible alert, **When** I click the close button, **Then** the alert disappears
3. **Given** an alert with action, **When** I click the action button, **Then** the specified action executes
4. **Given** multiple alerts, **When** displayed together, **Then** they stack vertically with spacing

---

### Toast Notification Component

**Purpose**: Show temporary, non-blocking messages that auto-dismiss.

**Props**:
```typescript
interface ToastProps {
  variant: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number; // ms, default: 3000
  position?: 'top-right' | 'top-center' | 'bottom-right' | 'bottom-center';
  onClose?: () => void;
}
```

**Visual Specifications**:
- Fixed positioning based on `position` prop
- Min width: 300px, max width: 500px
- Padding: 16px
- Border radius: 8px
- Drop shadow for elevation
- Slide-in animation on appear
- Fade-out animation on dismiss
- Progress bar at bottom showing time remaining

**Behavior**:
- Auto-dismiss after specified duration
- Hover pauses auto-dismiss timer
- Multiple toasts stack with spacing
- Maximum 3 visible at once (queue additional)

**Accessibility**:
- `role="status"` or `role="alert"`
- Announced to screen readers
- Can be dismissed with Escape key when focused

**Acceptance Criteria**:
1. **Given** a toast appears, **When** timer expires, **Then** it auto-dismisses with fade animation
2. **Given** I hover over a toast, **When** cursor is over it, **Then** auto-dismiss timer pauses
3. **Given** multiple toasts appear, **When** more than 3 exist, **Then** they queue and appear as others dismiss

---

### LoadingSpinner Component

**Purpose**: Indicate loading or processing state to users.

**Variants**:
- **Spinner**: Circular rotating indicator
- **Dots**: Three pulsing dots
- **Bar**: Linear progress bar

**Sizes**:
- Small: 16px
- Medium: 24px (default)
- Large: 40px
- Full: Covers entire container

**Props**:
```typescript
interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large' | 'full';
  variant?: 'spinner' | 'dots' | 'bar';
  text?: string; // Optional loading message
  overlay?: boolean; // Covers entire screen
}
```

**Visual Specifications**:

**Spinner**:
- Circular border with animated rotation
- Primary color
- Smooth animation (1s rotation)

**Dots**:
- Three dots horizontally aligned
- Pulsing animation in sequence
- 8px × 8px each dot

**Bar**:
- Full width of container
- 4px height
- Indeterminate animation (left to right)

**Overlay Mode**:
- Semi-transparent backdrop (#000, 50% opacity)
- Centered spinner
- Prevents interaction with content behind
- Z-index: 9999

**Accessibility**:
- `role="status"`
- `aria-live="polite"`
- `aria-label` describes loading state
- Optional text announced to screen readers

**Acceptance Criteria**:
1. **Given** content is loading, **When** spinner displays, **Then** I see smooth animation
2. **Given** overlay mode, **When** spinner is active, **Then** I cannot interact with content behind
3. **Given** loading completes, **When** spinner is removed, **Then** it fades out smoothly

---

## Layout Components

### Card Component

**Purpose**: Container component for grouping related content with consistent styling.

**Variants**:
- **Default**: Standard padding and border
- **Interactive**: Hover effect, clickable
- **Elevated**: Drop shadow for emphasis

**Props**:
```typescript
interface CardProps {
  children: React.ReactNode;
  variant?: 'default' | 'interactive' | 'elevated';
  padding?: 'none' | 'small' | 'medium' | 'large';
  onClick?: () => void;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}
```

**Visual Specifications**:
- Background: White
- Border: 1px solid light grey
- Border radius: 8px
- Padding:
  - None: 0px
  - Small: 12px
  - Medium: 16px (default)
  - Large: 24px

**Variants**:
```css
Default:
  - Border: 1px solid #E5E7EB
  - No shadow

Interactive:
  - Border: 1px solid #E5E7EB
  - Hover: shadow-md, slight scale up
  - Cursor: pointer
  - Transition: smooth (150ms)

Elevated:
  - Border: none
  - Shadow: shadow-lg
  - Hover: shadow-xl
```

**Card Header/Footer**:
- Header: Bold text, border bottom
- Footer: Muted text, border top
- Both optional

**Acceptance Criteria**:
1. **Given** an interactive card, **When** I hover over it, **Then** I see hover effects (shadow, scale)
2. **Given** an elevated card, **When** displayed, **Then** it has visible drop shadow
3. **Given** a card with header and footer, **When** rendered, **Then** they are visually separated from content

---

### Modal/Dialog Component

**Purpose**: Display content in an overlay that requires user attention or action.

**Props**:
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'small' | 'medium' | 'large' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
}
```

**Visual Specifications**:

**Overlay**:
- Background: Black with 50% opacity
- Fixed positioning, covers viewport
- Z-index: 1000
- Click to close (if enabled)

**Modal Container**:
- Background: White
- Border radius: 12px
- Max height: 90vh (scrollable if needed)
- Drop shadow: shadow-2xl
- Padding: 24px
- Centered in viewport

**Sizes**:
```
Small:  max-width: 400px
Medium: max-width: 600px (default)
Large:  max-width: 900px
Full:   width: 95vw, height: 95vh
```

**Header**:
- Title: Bold, 20px
- Close button (X) on right
- Border bottom: 1px solid light grey
- Padding bottom: 16px

**Content**:
- Scrollable if exceeds max height
- Padding: 16px 0

**Footer**:
- Border top: 1px solid light grey
- Padding top: 16px
- Right-aligned buttons
- Gap between buttons: 12px

**Animations**:
- Fade in/out for overlay (200ms)
- Scale and fade for modal (250ms)
- Smooth transitions

**Accessibility**:
- `role="dialog"`
- `aria-modal="true"`
- `aria-labelledby` points to title
- Focus trap within modal
- Escape key closes (if enabled)
- Focus returns to trigger on close
- Prevents body scroll when open

**Acceptance Criteria**:
1. **Given** a modal is open, **When** I press Escape, **Then** the modal closes (if enabled)
2. **Given** a modal is open, **When** I click outside (overlay), **Then** it closes (if enabled)
3. **Given** a modal is open, **When** I press Tab, **Then** focus cycles through modal elements only
4. **Given** a modal closes, **When** close completes, **Then** focus returns to trigger element
5. **Given** a modal has scrollable content, **When** content exceeds height, **Then** I can scroll within modal

---

### Separator/Divider Component

**Purpose**: Visual separator between content sections.

**Variants**:
- Horizontal (default)
- Vertical

**Props**:
```typescript
interface SeparatorProps {
  orientation?: 'horizontal' | 'vertical';
  spacing?: 'small' | 'medium' | 'large';
  variant?: 'solid' | 'dashed';
}
```

**Visual Specifications**:
- Color: Light grey (#E5E7EB)
- Thickness: 1px
- Margin:
  - Small: 8px
  - Medium: 16px (default)
  - Large: 24px

**Acceptance Criteria**:
1. **Given** a horizontal separator, **When** rendered, **Then** it spans full container width
2. **Given** a vertical separator, **When** rendered, **Then** it spans full container height

---

## Design System Tokens

### Colors

**Primary Palette**:
- Primary: #3B82F6 (blue)
- Primary Dark: #2563EB
- Primary Light: #60A5FA

**Semantic Colors**:
- Success: #10B981 (green)
- Error: #DC2626 (red)
- Warning: #F59E0B (orange)
- Info: #3B82F6 (blue)

**Neutral Palette**:
- Grey 50: #F9FAFB (lightest)
- Grey 100: #F3F4F6
- Grey 200: #E5E7EB
- Grey 300: #D1D5DB
- Grey 400: #9CA3AF
- Grey 500: #6B7280
- Grey 600: #4B5563
- Grey 700: #374151
- Grey 800: #1F2937
- Grey 900: #111827 (darkest)

**Text Colors**:
- Primary Text: Grey 900
- Secondary Text: Grey 600
- Disabled Text: Grey 400
- Link: Primary
- Link Hover: Primary Dark

### Typography

**Font Family**:
- Primary: System font stack (Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)
- Monospace: "SF Mono", Monaco, "Cascadia Code", monospace

**Font Sizes**:
```
xs:   12px (0.75rem)
sm:   14px (0.875rem)
base: 16px (1rem)
lg:   18px (1.125rem)
xl:   20px (1.25rem)
2xl:  24px (1.5rem)
3xl:  30px (1.875rem)
4xl:  36px (2.25rem)
```

**Font Weights**:
```
normal:   400
medium:   500
semibold: 600
bold:     700
```

**Line Heights**:
```
tight:   1.25
normal:  1.5
relaxed: 1.75
```

### Spacing

**Spacing Scale** (based on 4px):
```
0:  0px
1:  4px    (0.25rem)
2:  8px    (0.5rem)
3:  12px   (0.75rem)
4:  16px   (1rem)
5:  20px   (1.25rem)
6:  24px   (1.5rem)
8:  32px   (2rem)
10: 40px   (2.5rem)
12: 48px   (3rem)
16: 64px   (4rem)
20: 80px   (5rem)
```

### Border Radius

```
none: 0px
sm:   4px
md:   6px
lg:   8px
xl:   12px
2xl:  16px
full: 9999px (pill shape)
```

### Shadows

```
sm:   0 1px 2px 0 rgb(0 0 0 / 0.05)
md:   0 4px 6px -1px rgb(0 0 0 / 0.1)
lg:   0 10px 15px -3px rgb(0 0 0 / 0.1)
xl:   0 20px 25px -5px rgb(0 0 0 / 0.1)
2xl:  0 25px 50px -12px rgb(0 0 0 / 0.25)
```

### Breakpoints

```
sm:  640px   (mobile landscape)
md:  768px   (tablet)
lg:  1024px  (laptop)
xl:  1280px  (desktop)
2xl: 1536px  (large desktop)
```

### Z-Index Scale

```
base:     0
dropdown: 100
sticky:   200
fixed:    300
modal:    1000
popover:  1100
tooltip:  1200
toast:    1300
```

---

## Accessibility Standards

### Keyboard Navigation

**All interactive elements must support**:
- Tab/Shift+Tab: Navigate between elements
- Enter/Space: Activate buttons
- Escape: Close modals/dropdowns
- Arrow keys: Navigate within menus/lists

**Focus Management**:
- Visible focus indicators (2px outline)
- Skip navigation links for main content
- Focus trap in modals
- Logical tab order

### Screen Reader Support

**All components must**:
- Use semantic HTML (button, nav, header, etc.)
- Have appropriate ARIA labels
- Announce state changes with aria-live
- Describe interactive elements clearly
- Not rely on visual cues alone

### Color Contrast

**WCAG AA Standards (minimum)**:
- Normal text (< 18px): 4.5:1 contrast ratio
- Large text (≥ 18px): 3:1 contrast ratio
- Interactive elements: 3:1 contrast ratio

**Color Independence**:
- Don't rely solely on color to convey information
- Use icons, text, or patterns alongside color
- Consider colorblind users

### Touch Targets

**Minimum sizes**:
- Mobile: 44px × 44px
- Desktop: 40px × 40px
- Spacing between targets: min 8px

---

## Responsive Design Guidelines

### Mobile-First Approach

Start with mobile design, then enhance for larger screens.

### Breakpoint Strategy

```
Mobile:   < 640px (base styles)
Tablet:   640px - 1024px
Desktop:  > 1024px
```

### Common Patterns

**Mobile (< 640px)**:
- Single column layout
- Full-width buttons
- Hamburger menu for navigation
- Larger touch targets
- Simplified interfaces

**Tablet (640px - 1024px)**:
- Two-column layouts
- Visible navigation
- Standard button sizes
- More content density

**Desktop (> 1024px)**:
- Multi-column layouts
- Fixed sidebar navigation
- Hover states active
- Maximum content width (1200px)

---

## Success Criteria

### Consistency

- **SC-001**: All buttons maintain consistent styling across the application
- **SC-002**: All form inputs follow the same visual pattern
- **SC-003**: Color usage is consistent with design tokens throughout
- **SC-004**: Spacing follows the defined spacing scale (no arbitrary values)
- **SC-005**: All interactive elements have consistent hover and focus states

### Accessibility

- **SC-006**: All components meet WCAG AA contrast requirements
- **SC-007**: All interactive elements are keyboard accessible
- **SC-008**: Screen readers can navigate and understand all components
- **SC-009**: Focus indicators are visible on all interactive elements
- **SC-010**: Touch targets meet minimum size requirements (44px mobile)

### Performance

- **SC-011**: Components render without causing layout shift
- **SC-012**: Animations complete smoothly at 60fps
- **SC-013**: Modal open/close transitions complete within 300ms
- **SC-014**: Buttons respond to clicks within 100ms

### Usability

- **SC-015**: Users can identify button purpose by visual hierarchy alone
- **SC-016**: Error states provide clear guidance for resolution
- **SC-017**: Loading states indicate progress clearly
- **SC-018**: Modal/dialog focus behavior feels natural to users
- **SC-019**: Forms validate input appropriately without frustrating users
- **SC-020**: 95% of users understand component purpose without instruction

---

## Assumptions

- Modern browsers support (Chrome, Firefox, Safari, Edge - last 2 versions)
- CSS Grid and Flexbox are available
- CSS custom properties (variables) supported
- JavaScript enabled for interactive components
- Standard viewport sizes (320px - 1920px)
- Touch and mouse input supported
- No Internet Explorer support required
- Components built as reusable units
- Design system tokens used consistently

---

## Dependencies

- CSS-in-JS library OR Tailwind CSS for styling
- Icon library (Lucide, Heroicons, or similar)
- Focus-trap library for modal accessibility
- Animation library or CSS transitions
- State management for global UI state (modals, toasts)

---

## Future Considerations

- Dark mode support
- Theme customization system
- Additional component variants
- Animation presets library
- Skeleton loading states
- Empty state illustrations
- Advanced data table component
- Chart/visualization components
- File upload component
- Rich text editor component
- Multi-select dropdown
- Date picker component
- Command palette / search
