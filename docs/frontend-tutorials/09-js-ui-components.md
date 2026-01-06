# Tutorial 09: JavaScript UI Components — Tooltips, Toasts, and Modals

**What you'll learn:** How to build interactive UI components from scratch using vanilla JavaScript and CSS. No frameworks required.

**Time to complete:** 3-4 hours

**Prerequisites:** Basic JavaScript (DOM, events), CSS (positioning, transitions)

---

## Part 0: Why Build From Scratch?

### The Options

| Approach | Pros | Cons |
|----------|------|------|
| **CSS-only** | No JS, simple | Limited interactivity |
| **Vanilla JS** | Full control, no dependencies | More code to write |
| **Library (Bootstrap, etc.)** | Quick setup | Bundle size, customization limits |
| **Framework (React, Vue)** | Component reusability | Overkill for simple apps |

**Recommendation:** Learn vanilla JS first. You'll understand what libraries do, and you'll be able to build exactly what you need without bloat.

---

## Part 1: Tooltips

### The Goal

Hover over an element → Show helpful text → Mouse leaves → Text disappears.

### CSS-Only Tooltip (Simple Version)

```html
<button class="tooltip-trigger" data-tooltip="Import a new part file">
  Import
</button>
```

```css
.tooltip-trigger {
  position: relative;  /* Anchor for absolute positioning */
  cursor: pointer;
}

/* The tooltip box */
.tooltip-trigger::after {
  content: attr(data-tooltip);  /* Read from data attribute */
  
  /* Positioning */
  position: absolute;
  bottom: 100%;              /* Above the element */
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  
  /* Styling */
  background: #1a1a1a;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  white-space: nowrap;
  
  /* Hidden by default */
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s, visibility 0.15s;
  
  /* Above other content */
  z-index: 1000;
}

/* Arrow */
.tooltip-trigger::before {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 4px;
  
  border: 6px solid transparent;
  border-top-color: #1a1a1a;
  
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s, visibility 0.15s;
}

/* Show on hover */
.tooltip-trigger:hover::after,
.tooltip-trigger:hover::before {
  opacity: 1;
  visibility: visible;
}
```

### JavaScript Tooltip (Advanced Version)

For more control (positioning, delay, programmatic triggers):

```html
<button data-tooltip="Import a new part file">Import</button>
<button data-tooltip="Export current data">Export</button>
<button data-tooltip="Delete selected items" data-tooltip-position="right">Delete</button>
```

```css
/* Tooltip container (created by JS) */
.tooltip {
  position: fixed;
  background: #1a1a1a;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  white-space: nowrap;
  z-index: 10000;
  pointer-events: none;
  
  opacity: 0;
  transition: opacity 0.15s;
}

.tooltip.visible {
  opacity: 1;
}

/* Arrow for different positions */
.tooltip[data-position="top"]::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #1a1a1a;
}

.tooltip[data-position="bottom"]::after {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-bottom-color: #1a1a1a;
}

.tooltip[data-position="left"]::after {
  content: '';
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 6px solid transparent;
  border-left-color: #1a1a1a;
}

.tooltip[data-position="right"]::after {
  content: '';
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 6px solid transparent;
  border-right-color: #1a1a1a;
}
```

```javascript
/**
 * Tooltip system
 * 
 * Usage:
 *   <button data-tooltip="Help text">Button</button>
 *   <button data-tooltip="More text" data-tooltip-position="right">Button</button>
 */

class TooltipManager {
  constructor() {
    this.tooltip = null;
    this.currentTrigger = null;
    this.showDelay = 300;  // ms before showing
    this.hideDelay = 100;  // ms before hiding
    this.showTimeout = null;
    this.hideTimeout = null;
    
    this.init();
  }
  
  init() {
    // Create tooltip element
    this.tooltip = document.createElement('div');
    this.tooltip.className = 'tooltip';
    this.tooltip.setAttribute('role', 'tooltip');
    document.body.appendChild(this.tooltip);
    
    // Event delegation for all [data-tooltip] elements
    document.addEventListener('mouseenter', (e) => {
      const trigger = e.target.closest('[data-tooltip]');
      if (trigger) this.scheduleShow(trigger);
    }, true);
    
    document.addEventListener('mouseleave', (e) => {
      const trigger = e.target.closest('[data-tooltip]');
      if (trigger) this.scheduleHide();
    }, true);
    
    // Hide on scroll
    document.addEventListener('scroll', () => this.hide(), true);
  }
  
  scheduleShow(trigger) {
    clearTimeout(this.hideTimeout);
    this.showTimeout = setTimeout(() => {
      this.show(trigger);
    }, this.showDelay);
  }
  
  scheduleHide() {
    clearTimeout(this.showTimeout);
    this.hideTimeout = setTimeout(() => {
      this.hide();
    }, this.hideDelay);
  }
  
  show(trigger) {
    const text = trigger.getAttribute('data-tooltip');
    const position = trigger.getAttribute('data-tooltip-position') || 'top';
    
    this.tooltip.textContent = text;
    this.tooltip.setAttribute('data-position', position);
    this.tooltip.classList.add('visible');
    
    this.position(trigger, position);
    this.currentTrigger = trigger;
  }
  
  hide() {
    this.tooltip.classList.remove('visible');
    this.currentTrigger = null;
  }
  
  position(trigger, position) {
    const triggerRect = trigger.getBoundingClientRect();
    const tooltipRect = this.tooltip.getBoundingClientRect();
    const gap = 8;  // Gap between trigger and tooltip
    
    let top, left;
    
    switch (position) {
      case 'top':
        top = triggerRect.top - tooltipRect.height - gap;
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
        break;
      case 'bottom':
        top = triggerRect.bottom + gap;
        left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
        left = triggerRect.left - tooltipRect.width - gap;
        break;
      case 'right':
        top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
        left = triggerRect.right + gap;
        break;
    }
    
    // Keep on screen
    top = Math.max(8, Math.min(top, window.innerHeight - tooltipRect.height - 8));
    left = Math.max(8, Math.min(left, window.innerWidth - tooltipRect.width - 8));
    
    this.tooltip.style.top = `${top}px`;
    this.tooltip.style.left = `${left}px`;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new TooltipManager();
});
```

---

## Part 2: Toast Notifications

### The Goal

Show temporary messages that appear and auto-dismiss:

```
┌──────────────────────────────────┐
│ ✓ Part imported successfully     │ ← Appears
│                                  │ ← Stays for 3 seconds
└──────────────────────────────────┘ ← Fades away
```

### The CSS

```css
/* Toast container (anchors toasts to bottom-right) */
.toast-container {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  z-index: 10000;
}

/* Individual toast */
.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #1a1a1a;
  color: white;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 300px;
  max-width: 450px;
  
  /* Animation */
  animation: toast-in 0.3s ease-out;
}

.toast.removing {
  animation: toast-out 0.3s ease-in forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

/* Toast variants */
.toast-success {
  background: #16a34a;
}

.toast-error {
  background: #dc2626;
}

.toast-warning {
  background: #d97706;
}

.toast-info {
  background: #2563eb;
}

/* Toast icon */
.toast-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

/* Toast content */
.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 0.125rem;
}

.toast-message {
  font-size: 0.875rem;
  opacity: 0.9;
}

/* Close button */
.toast-close {
  background: none;
  border: none;
  color: white;
  opacity: 0.7;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1.25rem;
  line-height: 1;
}

.toast-close:hover {
  opacity: 1;
}
```

### The JavaScript

```javascript
/**
 * Toast notification system
 * 
 * Usage:
 *   toast.success('Part imported successfully');
 *   toast.error('Failed to import file', 'File not found');
 *   toast.warning('Unsaved changes');
 *   toast.info('New version available');
 */

class ToastManager {
  constructor() {
    this.container = null;
    this.defaultDuration = 4000;  // 4 seconds
    this.init();
  }
  
  init() {
    this.container = document.createElement('div');
    this.container.className = 'toast-container';
    this.container.setAttribute('role', 'alert');
    this.container.setAttribute('aria-live', 'polite');
    document.body.appendChild(this.container);
  }
  
  show(options) {
    const {
      type = 'info',
      title = '',
      message = '',
      duration = this.defaultDuration
    } = options;
    
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type]}</span>
      <div class="toast-content">
        ${title ? `<div class="toast-title">${title}</div>` : ''}
        ${message ? `<div class="toast-message">${message}</div>` : ''}
      </div>
      <button class="toast-close" aria-label="Dismiss">×</button>
    `;
    
    // Add close handler
    toast.querySelector('.toast-close').addEventListener('click', () => {
      this.dismiss(toast);
    });
    
    // Add to container
    this.container.appendChild(toast);
    
    // Auto-dismiss
    if (duration > 0) {
      setTimeout(() => this.dismiss(toast), duration);
    }
    
    return toast;
  }
  
  dismiss(toast) {
    if (!toast || !toast.parentElement) return;
    
    toast.classList.add('removing');
    setTimeout(() => {
      toast.remove();
    }, 300);  // Match animation duration
  }
  
  // Convenience methods
  success(message, title = '') {
    return this.show({ type: 'success', title, message });
  }
  
  error(message, title = 'Error') {
    return this.show({ type: 'error', title, message });
  }
  
  warning(message, title = '') {
    return this.show({ type: 'warning', title, message });
  }
  
  info(message, title = '') {
    return this.show({ type: 'info', title, message });
  }
}

// Global instance
const toast = new ToastManager();
```

### Usage Examples

```javascript
// Simple messages
toast.success('Part saved successfully');
toast.error('Failed to save');
toast.warning('Unsaved changes');

// With title
toast.success('Import Complete', 'Bracket.xml imported with 12 operations');
toast.error('Import Failed', 'File not found: C:\\Parts\\missing.xml');

// Custom duration
toast.show({
  type: 'info',
  title: 'Reminder',
  message: 'This will stay longer',
  duration: 8000  // 8 seconds
});

// Never auto-dismiss
toast.show({
  type: 'warning',
  message: 'Click X to dismiss',
  duration: 0
});
```

---

## Part 3: Modals / Dialogs

### The Goal

A centered overlay with content that blocks interaction with the page behind.

```
┌─────────────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░ ┌───────────────────────────────────┐ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ │ Confirm Delete                  ✕ │ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ ├───────────────────────────────────┤ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ │                                   │ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ │ Are you sure you want to delete   │ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ │ "Bracket Assembly"?               │ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ │                                   │ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ ├───────────────────────────────────┤ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ │            [Cancel]  [Delete]     │ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░ └───────────────────────────────────┘ ░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────────────────────────────────────┘
       ↑ Darkened background (click to close)
```

### The CSS

```css
/* Modal backdrop */
.modal-backdrop {
  position: fixed;
  inset: 0;  /* top: 0; right: 0; bottom: 0; left: 0 */
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  
  /* Animation */
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s, visibility 0.2s;
}

.modal-backdrop.open {
  opacity: 1;
  visibility: visible;
}

/* Modal box */
.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: auto;
  
  /* Animation */
  transform: scale(0.95);
  transition: transform 0.2s;
}

.modal-backdrop.open .modal {
  transform: scale(1);
}

/* Modal header */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e5e5;
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
}

.modal-close:hover {
  color: #1a1a1a;
}

/* Modal body */
.modal-body {
  padding: 1.25rem;
}

/* Modal footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #e5e5e5;
}

/* Modal sizes */
.modal.modal-sm { max-width: 350px; }
.modal.modal-lg { max-width: 700px; }
.modal.modal-xl { max-width: 900px; }
```

### The JavaScript

```javascript
/**
 * Modal dialog system
 * 
 * Usage:
 *   modal.confirm({
 *     title: 'Delete Part?',
 *     message: 'This cannot be undone.',
 *     confirmText: 'Delete',
 *     confirmClass: 'btn-danger',
 *     onConfirm: () => deletePart(id)
 *   });
 *   
 *   modal.alert({
 *     title: 'Error',
 *     message: 'Something went wrong.'
 *   });
 */

class ModalManager {
  constructor() {
    this.backdrop = null;
    this.currentModal = null;
    this.previousFocus = null;
    this.init();
  }
  
  init() {
    // Create backdrop
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'modal-backdrop';
    document.body.appendChild(this.backdrop);
    
    // Close on backdrop click
    this.backdrop.addEventListener('click', (e) => {
      if (e.target === this.backdrop) {
        this.close();
      }
    });
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.currentModal) {
        this.close();
      }
    });
  }
  
  open(options) {
    const {
      title = '',
      content = '',
      size = '',
      footer = null,
      onClose = null
    } = options;
    
    // Save current focus
    this.previousFocus = document.activeElement;
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = `modal ${size ? `modal-${size}` : ''}`;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    if (title) modal.setAttribute('aria-labelledby', 'modal-title');
    
    modal.innerHTML = `
      <div class="modal-header">
        <h2 class="modal-title" id="modal-title">${title}</h2>
        <button class="modal-close" aria-label="Close">×</button>
      </div>
      <div class="modal-body">
        ${typeof content === 'string' ? content : ''}
      </div>
      ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
    `;
    
    // If content is an element, append it
    if (content instanceof Element) {
      modal.querySelector('.modal-body').appendChild(content);
    }
    
    // Close button handler
    modal.querySelector('.modal-close').addEventListener('click', () => {
      this.close();
    });
    
    // Add to backdrop
    this.backdrop.innerHTML = '';
    this.backdrop.appendChild(modal);
    this.currentModal = modal;
    this.onCloseCallback = onClose;
    
    // Open
    requestAnimationFrame(() => {
      this.backdrop.classList.add('open');
      // Focus first focusable element
      const focusable = modal.querySelector('button, input, select, textarea, [tabindex]');
      if (focusable) focusable.focus();
    });
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    return modal;
  }
  
  close() {
    if (!this.currentModal) return;
    
    this.backdrop.classList.remove('open');
    
    setTimeout(() => {
      this.backdrop.innerHTML = '';
      this.currentModal = null;
      
      // Restore body scroll
      document.body.style.overflow = '';
      
      // Restore focus
      if (this.previousFocus) {
        this.previousFocus.focus();
      }
      
      // Call onClose callback
      if (this.onCloseCallback) {
        this.onCloseCallback();
        this.onCloseCallback = null;
      }
    }, 200);  // Match CSS transition duration
  }
  
  // Convenience: Alert dialog
  alert({ title = 'Alert', message = '' }) {
    return new Promise((resolve) => {
      this.open({
        title,
        content: `<p>${message}</p>`,
        footer: `<button class="btn btn-primary modal-ok">OK</button>`,
        onClose: resolve
      });
      
      this.currentModal.querySelector('.modal-ok').addEventListener('click', () => {
        this.close();
      });
    });
  }
  
  // Convenience: Confirm dialog
  confirm({
    title = 'Confirm',
    message = '',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    confirmClass = 'btn-primary',
    onConfirm = null,
    onCancel = null
  }) {
    return new Promise((resolve) => {
      this.open({
        title,
        content: `<p>${message}</p>`,
        footer: `
          <button class="btn btn-secondary modal-cancel">${cancelText}</button>
          <button class="btn ${confirmClass} modal-confirm">${confirmText}</button>
        `
      });
      
      this.currentModal.querySelector('.modal-cancel').addEventListener('click', () => {
        if (onCancel) onCancel();
        this.close();
        resolve(false);
      });
      
      this.currentModal.querySelector('.modal-confirm').addEventListener('click', () => {
        if (onConfirm) onConfirm();
        this.close();
        resolve(true);
      });
    });
  }
  
  // Convenience: Custom content modal
  custom({ title, content, size, onClose }) {
    return this.open({ title, content, size, onClose });
  }
}

// Global instance
const modal = new ModalManager();
```

### Usage Examples

```javascript
// Simple alert
modal.alert({
  title: 'Success',
  message: 'Part imported successfully!'
});

// Confirm dialog
modal.confirm({
  title: 'Delete Part?',
  message: 'Are you sure you want to delete "Bracket Assembly"? This cannot be undone.',
  confirmText: 'Delete',
  confirmClass: 'btn-danger',
  onConfirm: () => {
    deletePart('bracket');
    toast.success('Part deleted');
  }
});

// Async/await pattern
async function handleDelete() {
  const confirmed = await modal.confirm({
    title: 'Confirm Delete',
    message: 'This action cannot be undone.'
  });
  
  if (confirmed) {
    await deletePart();
    toast.success('Deleted');
  }
}

// Custom content
modal.custom({
  title: 'Quick Import',
  size: 'sm',
  content: `
    <form id="quick-import-form">
      <div class="form-group">
        <label class="form-label">Part Name</label>
        <input type="text" class="form-input" name="name" required>
      </div>
      <div class="form-group">
        <label class="form-label">Machine</label>
        <input type="text" class="form-input" name="machine" required>
      </div>
      <button type="submit" class="btn btn-primary">Import</button>
    </form>
  `
});
```

---

## Part 4: Complete Working Example

Create `ui-components.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI Components Demo</title>
  <style>
    /* Reset */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #f5f5f5;
      padding: 2rem;
      line-height: 1.6;
    }
    
    .container {
      max-width: 600px;
      margin: 0 auto;
    }
    
    h1 { margin-bottom: 0.5rem; }
    h2 { margin: 2rem 0 1rem; font-size: 1.25rem; }
    p { color: #666; margin-bottom: 1.5rem; }
    
    .demo-row {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    
    /* Buttons */
    .btn {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    
    .btn-primary { background: #2563eb; color: white; }
    .btn-primary:hover { background: #1d4ed8; }
    .btn-secondary { background: white; border: 1px solid #e5e5e5; color: #666; }
    .btn-secondary:hover { border-color: #999; }
    .btn-success { background: #16a34a; color: white; }
    .btn-danger { background: #dc2626; color: white; }
    
    /* Form elements */
    .form-group { margin-bottom: 1rem; }
    .form-label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.25rem; }
    .form-input { 
      width: 100%; 
      padding: 0.5rem 0.75rem; 
      border: 1px solid #e5e5e5; 
      border-radius: 6px;
      font-size: 1rem;
    }
    
    /* ========== TOOLTIP STYLES ========== */
    .tooltip {
      position: fixed;
      background: #1a1a1a;
      color: white;
      padding: 0.5rem 0.75rem;
      border-radius: 4px;
      font-size: 0.75rem;
      white-space: nowrap;
      z-index: 10000;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.15s;
    }
    
    .tooltip.visible { opacity: 1; }
    
    .tooltip[data-position="top"]::after {
      content: '';
      position: absolute;
      top: 100%;
      left: 50%;
      transform: translateX(-50%);
      border: 6px solid transparent;
      border-top-color: #1a1a1a;
    }
    
    .tooltip[data-position="bottom"]::after {
      content: '';
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%);
      border: 6px solid transparent;
      border-bottom-color: #1a1a1a;
    }
    
    /* ========== TOAST STYLES ========== */
    .toast-container {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      z-index: 10000;
    }
    
    .toast {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      background: #1a1a1a;
      color: white;
      padding: 1rem 1.25rem;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      min-width: 280px;
      animation: toast-in 0.3s ease-out;
    }
    
    .toast.removing { animation: toast-out 0.3s ease-in forwards; }
    
    @keyframes toast-in {
      from { opacity: 0; transform: translateX(100%); }
      to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes toast-out {
      from { opacity: 1; transform: translateX(0); }
      to { opacity: 0; transform: translateX(100%); }
    }
    
    .toast-success { background: #16a34a; }
    .toast-error { background: #dc2626; }
    .toast-warning { background: #d97706; }
    .toast-info { background: #2563eb; }
    
    .toast-icon { font-size: 1.25rem; }
    .toast-content { flex: 1; }
    .toast-title { font-weight: 600; }
    .toast-message { font-size: 0.875rem; opacity: 0.9; }
    .toast-close {
      background: none; border: none; color: white;
      opacity: 0.7; cursor: pointer; font-size: 1.25rem;
    }
    .toast-close:hover { opacity: 1; }
    
    /* ========== MODAL STYLES ========== */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10000;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.2s, visibility 0.2s;
    }
    
    .modal-backdrop.open {
      opacity: 1;
      visibility: visible;
    }
    
    .modal {
      background: white;
      border-radius: 8px;
      box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
      max-width: 500px;
      width: 90%;
      transform: scale(0.95);
      transition: transform 0.2s;
    }
    
    .modal-backdrop.open .modal { transform: scale(1); }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid #e5e5e5;
    }
    
    .modal-title { font-size: 1.125rem; font-weight: 600; }
    
    .modal-close {
      background: none; border: none; font-size: 1.5rem;
      color: #666; cursor: pointer;
    }
    
    .modal-body { padding: 1.25rem; }
    
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      padding: 1rem 1.25rem;
      border-top: 1px solid #e5e5e5;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>UI Components</h1>
    <p>Interactive tooltips, toasts, and modals built with vanilla JavaScript.</p>
    
    <h2>Tooltips</h2>
    <div class="demo-row">
      <button class="btn btn-secondary" data-tooltip="Import a new part from XML">
        Hover me (top)
      </button>
      <button class="btn btn-secondary" data-tooltip="More info here" data-tooltip-position="bottom">
        Bottom tooltip
      </button>
    </div>
    
    <h2>Toast Notifications</h2>
    <div class="demo-row">
      <button class="btn btn-success" onclick="toast.success('Part saved successfully!')">
        Success Toast
      </button>
      <button class="btn btn-danger" onclick="toast.error('Something went wrong', 'Error')">
        Error Toast
      </button>
      <button class="btn btn-secondary" onclick="toast.info('New version available')">
        Info Toast
      </button>
    </div>
    
    <h2>Modal Dialogs</h2>
    <div class="demo-row">
      <button class="btn btn-primary" onclick="showAlert()">
        Alert
      </button>
      <button class="btn btn-danger" onclick="showConfirm()">
        Confirm Delete
      </button>
      <button class="btn btn-secondary" onclick="showCustom()">
        Custom Modal
      </button>
    </div>
  </div>
  
  <script>
    // ========== TOOLTIP MANAGER ==========
    class TooltipManager {
      constructor() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tooltip';
        document.body.appendChild(this.tooltip);
        
        document.addEventListener('mouseenter', (e) => {
          const trigger = e.target.closest('[data-tooltip]');
          if (trigger) this.show(trigger);
        }, true);
        
        document.addEventListener('mouseleave', (e) => {
          const trigger = e.target.closest('[data-tooltip]');
          if (trigger) this.hide();
        }, true);
      }
      
      show(trigger) {
        const text = trigger.getAttribute('data-tooltip');
        const position = trigger.getAttribute('data-tooltip-position') || 'top';
        
        this.tooltip.textContent = text;
        this.tooltip.setAttribute('data-position', position);
        this.tooltip.classList.add('visible');
        
        const rect = trigger.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        let top, left;
        if (position === 'top') {
          top = rect.top - tooltipRect.height - 8;
          left = rect.left + (rect.width - tooltipRect.width) / 2;
        } else {
          top = rect.bottom + 8;
          left = rect.left + (rect.width - tooltipRect.width) / 2;
        }
        
        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
      }
      
      hide() {
        this.tooltip.classList.remove('visible');
      }
    }
    
    // ========== TOAST MANAGER ==========
    class ToastManager {
      constructor() {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
      }
      
      show({ type = 'info', title = '', message = '' }) {
        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
          <span class="toast-icon">${icons[type]}</span>
          <div class="toast-content">
            ${title ? `<div class="toast-title">${title}</div>` : ''}
            <div class="toast-message">${message}</div>
          </div>
          <button class="toast-close">×</button>
        `;
        
        toast.querySelector('.toast-close').onclick = () => this.dismiss(toast);
        this.container.appendChild(toast);
        setTimeout(() => this.dismiss(toast), 4000);
      }
      
      dismiss(toast) {
        if (!toast.parentElement) return;
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
      }
      
      success(message, title = '') { this.show({ type: 'success', title, message }); }
      error(message, title = '') { this.show({ type: 'error', title, message }); }
      warning(message, title = '') { this.show({ type: 'warning', title, message }); }
      info(message, title = '') { this.show({ type: 'info', title, message }); }
    }
    
    // ========== MODAL MANAGER ==========
    class ModalManager {
      constructor() {
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'modal-backdrop';
        document.body.appendChild(this.backdrop);
        
        this.backdrop.onclick = (e) => {
          if (e.target === this.backdrop) this.close();
        };
        
        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape') this.close();
        });
      }
      
      open({ title, content, footer }) {
        this.backdrop.innerHTML = `
          <div class="modal">
            <div class="modal-header">
              <h2 class="modal-title">${title}</h2>
              <button class="modal-close">×</button>
            </div>
            <div class="modal-body">${content}</div>
            ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
          </div>
        `;
        
        this.backdrop.querySelector('.modal-close').onclick = () => this.close();
        this.backdrop.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
      
      close() {
        this.backdrop.classList.remove('open');
        setTimeout(() => {
          this.backdrop.innerHTML = '';
          document.body.style.overflow = '';
        }, 200);
      }
      
      alert({ title, message }) {
        this.open({
          title,
          content: `<p>${message}</p>`,
          footer: '<button class="btn btn-primary" onclick="modal.close()">OK</button>'
        });
      }
      
      confirm({ title, message, onConfirm }) {
        this.open({
          title,
          content: `<p>${message}</p>`,
          footer: `
            <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
            <button class="btn btn-danger" id="modal-confirm">Delete</button>
          `
        });
        
        document.getElementById('modal-confirm').onclick = () => {
          this.close();
          onConfirm();
        };
      }
    }
    
    // Initialize
    new TooltipManager();
    const toast = new ToastManager();
    const modal = new ModalManager();
    
    // Demo functions
    function showAlert() {
      modal.alert({
        title: 'Import Complete',
        message: 'Successfully imported Bracket.xml with 12 operations and 8 tools.'
      });
    }
    
    function showConfirm() {
      modal.confirm({
        title: 'Delete Part?',
        message: 'Are you sure you want to delete "Bracket Assembly"? This action cannot be undone.',
        onConfirm: () => toast.success('Part deleted successfully')
      });
    }
    
    function showCustom() {
      modal.open({
        title: 'Quick Import',
        content: `
          <form>
            <div class="form-group">
              <label class="form-label">Part Name</label>
              <input type="text" class="form-input" placeholder="Enter part name">
            </div>
            <div class="form-group">
              <label class="form-label">Machine</label>
              <input type="text" class="form-input" placeholder="e.g., Haas VF-2">
            </div>
          </form>
        `,
        footer: `
          <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
          <button class="btn btn-primary" onclick="modal.close(); toast.success('Part imported!')">Import</button>
        `
      });
    }
  </script>
</body>
</html>
```

---

## Summary

### What You Built

| Component | Trigger | Behavior |
|-----------|---------|----------|
| Tooltip | Hover | Show info, auto-position |
| Toast | Code call | Appear, auto-dismiss |
| Modal | Code call | Block interaction, require action |

### When to Use Each

| Need | Component |
|------|-----------|
| Help text for UI elements | Tooltip |
| Success/error feedback | Toast |
| Confirmation before action | Modal (confirm) |
| Display information | Modal (alert) |
| Collect quick input | Modal (custom) |

---

## Next Steps

- **[Tutorial 10: UI Libraries](./10-ui-libraries.md)** — DataTables, D3.js, CDN vs NPM
- **[Tutorial 08: Animations](./08-animations.md)** — CSS transitions and keyframes
