/**
 * Accessibility Integration for AI Browser
 * Provides access to Chrome's Accessibility APIs and semantic element understanding
 */

class AccessibilityIntegration {
    constructor() {
        this.debugMode = false;
        this.cache = new Map();
        this.cacheTimeout = 5000; // 5 seconds
    }

    log(...args) {
        if (this.debugMode) {
            console.log('[Accessibility]', ...args);
        }
    }

    /**
     * Get the accessibility tree for the page
     */
    async getAccessibilityTree(options = {}) {
        const {
            maxDepth = 5,
            includeInvisible = false,
            filterRoles = null,
            rootSelector = null
        } = options;

        try {
            // Use Chrome's accessibility API if available
            if (chrome?.accessibility) {
                return await this.getChromeAccessibilityTree(options);
            }

            // Fallback to DOM-based accessibility tree
            return await this.getDOMAccessibilityTree(options);
        } catch (error) {
            this.log('Error getting accessibility tree:', error);
            return { error: error.message };
        }
    }

    /**
     * Chrome DevTools Accessibility API integration
     */
    async getChromeAccessibilityTree(options) {
        return new Promise((resolve) => {
            // This would require DevTools protocol access
            // For now, fallback to DOM-based approach
            resolve(this.getDOMAccessibilityTree(options));
        });
    }

    /**
     * DOM-based accessibility tree extraction
     */
    async getDOMAccessibilityTree(options) {
        const {
            maxDepth = 5,
            includeInvisible = false,
            filterRoles = null,
            rootSelector = null
        } = options;

        const rootElement = rootSelector ? 
            document.querySelector(rootSelector) : 
            document.body;

        if (!rootElement) {
            return { error: 'Root element not found' };
        }

        const tree = this.buildAccessibilityNode(rootElement, 0, maxDepth, {
            includeInvisible,
            filterRoles
        });

        return {
            success: true,
            tree,
            metadata: {
                generated: Date.now(),
                maxDepth,
                rootElement: rootElement.tagName.toLowerCase()
            }
        };
    }

    /**
     * Build accessibility node information
     */
    buildAccessibilityNode(element, currentDepth, maxDepth, options) {
        if (currentDepth >= maxDepth) {
            return null;
        }

        // Skip invisible elements unless requested
        if (!options.includeInvisible && !this.isElementVisible(element)) {
            return null;
        }

        const node = {
            tagName: element.tagName.toLowerCase(),
            role: this.getElementRole(element),
            name: this.getAccessibleName(element),
            description: this.getAccessibleDescription(element),
            level: this.getHeadingLevel(element),
            expanded: this.getExpandedState(element),
            disabled: element.disabled || element.getAttribute('aria-disabled') === 'true',
            focusable: this.isElementFocusable(element),
            bounds: this.getElementBounds(element),
            selector: this.generateSelector(element),
            attributes: this.getRelevantAttributes(element),
            children: []
        };

        // Filter by roles if specified
        if (options.filterRoles && !options.filterRoles.includes(node.role)) {
            return null;
        }

        // Process children
        for (const child of element.children) {
            const childNode = this.buildAccessibilityNode(
                child, 
                currentDepth + 1, 
                maxDepth, 
                options
            );
            if (childNode) {
                node.children.push(childNode);
            }
        }

        return node;
    }

    /**
     * Find elements by accessibility properties
     */
    async findByAccessibility(criteria = {}) {
        const {
            role,
            name,
            description,
            level,
            expanded,
            maxResults = 10
        } = criteria;

        const results = [];
        const elements = document.querySelectorAll('*');

        for (const element of elements) {
            if (results.length >= maxResults) break;

            // Check role match
            if (role && this.getElementRole(element) !== role) continue;

            // Check name match
            if (name && !this.getAccessibleName(element).toLowerCase().includes(name.toLowerCase())) continue;

            // Check description match
            if (description && !this.getAccessibleDescription(element).toLowerCase().includes(description.toLowerCase())) continue;

            // Check level match (for headings)
            if (level !== undefined && this.getHeadingLevel(element) !== level) continue;

            // Check expanded state
            if (expanded !== undefined && this.getExpandedState(element) !== expanded) continue;

            results.push({
                element: element,
                tagName: element.tagName.toLowerCase(),
                role: this.getElementRole(element),
                name: this.getAccessibleName(element),
                description: this.getAccessibleDescription(element),
                level: this.getHeadingLevel(element),
                selector: this.generateSelector(element),
                bounds: this.getElementBounds(element)
            });
        }

        return {
            success: true,
            results,
            count: results.length,
            criteria
        };
    }

    /**
     * Get accessibility information for a specific element
     */
    getElementAccessibility(selector, includeChildren = false) {
        const element = document.querySelector(selector);
        if (!element) {
            return { error: 'Element not found' };
        }

        const info = {
            tagName: element.tagName.toLowerCase(),
            role: this.getElementRole(element),
            name: this.getAccessibleName(element),
            description: this.getAccessibleDescription(element),
            level: this.getHeadingLevel(element),
            expanded: this.getExpandedState(element),
            disabled: element.disabled || element.getAttribute('aria-disabled') === 'true',
            focusable: this.isElementFocusable(element),
            bounds: this.getElementBounds(element),
            attributes: this.getRelevantAttributes(element),
            computedRole: this.getComputedRole(element),
            states: this.getAriaStates(element)
        };

        if (includeChildren) {
            info.children = Array.from(element.children).map(child => ({
                tagName: child.tagName.toLowerCase(),
                role: this.getElementRole(child),
                name: this.getAccessibleName(child),
                selector: this.generateSelector(child)
            }));
        }

        return { success: true, info };
    }

    /**
     * Get page landmarks
     */
    getLandmarks(includeImplicit = true) {
        const landmarkRoles = ['navigation', 'main', 'banner', 'contentinfo', 'complementary', 'search', 'form'];
        const landmarks = [];

        // Explicit landmarks
        for (const role of landmarkRoles) {
            const elements = document.querySelectorAll(`[role="${role}"]`);
            elements.forEach(el => {
                landmarks.push({
                    role,
                    name: this.getAccessibleName(el),
                    selector: this.generateSelector(el),
                    bounds: this.getElementBounds(el),
                    explicit: true
                });
            });
        }

        // Implicit landmarks
        if (includeImplicit) {
            const implicitMappings = {
                'nav': 'navigation',
                'main': 'main',
                'header': 'banner',
                'footer': 'contentinfo',
                'aside': 'complementary',
                'form': 'form'
            };

            for (const [tag, role] of Object.entries(implicitMappings)) {
                const elements = document.querySelectorAll(tag);
                elements.forEach(el => {
                    // Skip if already has explicit role
                    if (el.getAttribute('role')) return;

                    landmarks.push({
                        role,
                        name: this.getAccessibleName(el),
                        selector: this.generateSelector(el),
                        bounds: this.getElementBounds(el),
                        explicit: false,
                        tagName: tag
                    });
                });
            }
        }

        return {
            success: true,
            landmarks,
            count: landmarks.length
        };
    }

    /**
     * Get page headings structure
     */
    getHeadings(minLevel = 1, maxLevel = 6, includeHidden = false) {
        const headings = [];
        
        for (let level = minLevel; level <= maxLevel; level++) {
            const elements = document.querySelectorAll(`h${level}`);
            elements.forEach(el => {
                if (!includeHidden && !this.isElementVisible(el)) return;

                headings.push({
                    level,
                    text: el.textContent.trim(),
                    name: this.getAccessibleName(el),
                    selector: this.generateSelector(el),
                    bounds: this.getElementBounds(el),
                    id: el.id || null
                });
            });
        }

        // Also check for elements with heading roles
        const roleHeadings = document.querySelectorAll('[role="heading"]');
        roleHeadings.forEach(el => {
            if (!includeHidden && !this.isElementVisible(el)) return;

            const level = parseInt(el.getAttribute('aria-level')) || 1;
            if (level >= minLevel && level <= maxLevel) {
                headings.push({
                    level,
                    text: el.textContent.trim(),
                    name: this.getAccessibleName(el),
                    selector: this.generateSelector(el),
                    bounds: this.getElementBounds(el),
                    role: 'heading'
                });
            }
        });

        // Sort by document order
        headings.sort((a, b) => {
            const aEl = document.querySelector(a.selector);
            const bEl = document.querySelector(b.selector);
            return aEl.compareDocumentPosition(bEl) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
        });

        return {
            success: true,
            headings,
            count: headings.length,
            structure: this.buildHeadingStructure(headings)
        };
    }

    /**
     * Build hierarchical heading structure
     */
    buildHeadingStructure(headings) {
        const structure = [];
        const stack = [];

        for (const heading of headings) {
            // Pop stack until we find a parent level
            while (stack.length > 0 && stack[stack.length - 1].level >= heading.level) {
                stack.pop();
            }

            const structureItem = { ...heading, children: [] };

            if (stack.length === 0) {
                structure.push(structureItem);
            } else {
                stack[stack.length - 1].children.push(structureItem);
            }

            stack.push(structureItem);
        }

        return structure;
    }

    /**
     * Get form controls with accessibility info
     */
    getFormControls(formSelector = null, includeLabels = true, includeValidation = true) {
        const forms = formSelector ? 
            [document.querySelector(formSelector)].filter(Boolean) :
            Array.from(document.forms);

        const controls = [];

        forms.forEach(form => {
            const formControls = form.querySelectorAll(
                'input:not([type="hidden"]), textarea, select, button[type="submit"], [role="button"], [role="textbox"], [role="combobox"], [role="checkbox"], [role="radio"]'
            );

            formControls.forEach(control => {
                const controlInfo = {
                    tagName: control.tagName.toLowerCase(),
                    type: control.type || 'unknown',
                    role: this.getElementRole(control),
                    name: this.getAccessibleName(control),
                    description: this.getAccessibleDescription(control),
                    required: control.required || control.getAttribute('aria-required') === 'true',
                    disabled: control.disabled || control.getAttribute('aria-disabled') === 'true',
                    selector: this.generateSelector(control),
                    bounds: this.getElementBounds(control)
                };

                if (includeLabels) {
                    controlInfo.labels = this.getAssociatedLabels(control);
                }

                if (includeValidation) {
                    controlInfo.validation = this.getValidationInfo(control);
                }

                controls.push(controlInfo);
            });
        });

        return {
            success: true,
            controls,
            count: controls.length,
            formsAnalyzed: forms.length
        };
    }

    /**
     * Utility methods
     */
    isElementVisible(element) {
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
    }

    isElementFocusable(element) {
        if (element.disabled) return false;
        if (element.tabIndex < 0) return false;
        if (element.tabIndex >= 0) return true;

        const focusableElements = [
            'a[href]', 'area[href]', 'input:not([disabled])', 
            'select:not([disabled])', 'textarea:not([disabled])', 
            'button:not([disabled])', 'iframe', 'object', 'embed',
            '[contenteditable]', '[tabindex]'
        ];

        return focusableElements.some(selector => element.matches(selector));
    }

    getElementRole(element) {
        // Explicit role
        const explicitRole = element.getAttribute('role');
        if (explicitRole) return explicitRole;

        // Implicit role based on tag
        const implicitRoles = {
            'a': 'link',
            'button': 'button',
            'input': this.getInputRole(element),
            'textarea': 'textbox',
            'select': 'combobox',
            'h1': 'heading',
            'h2': 'heading',
            'h3': 'heading',
            'h4': 'heading',
            'h5': 'heading',
            'h6': 'heading',
            'nav': 'navigation',
            'main': 'main',
            'header': 'banner',
            'footer': 'contentinfo',
            'aside': 'complementary',
            'section': 'region',
            'article': 'article',
            'ul': 'list',
            'ol': 'list',
            'li': 'listitem',
            'table': 'table',
            'form': 'form'
        };

        return implicitRoles[element.tagName.toLowerCase()] || 'generic';
    }

    getInputRole(element) {
        const type = element.type.toLowerCase();
        const roleMapping = {
            'text': 'textbox',
            'email': 'textbox',
            'password': 'textbox',
            'search': 'searchbox',
            'tel': 'textbox',
            'url': 'textbox',
            'number': 'spinbutton',
            'checkbox': 'checkbox',
            'radio': 'radio',
            'button': 'button',
            'submit': 'button',
            'reset': 'button',
            'range': 'slider'
        };

        return roleMapping[type] || 'textbox';
    }

    getAccessibleName(element) {
        // aria-label
        if (element.getAttribute('aria-label')) {
            return element.getAttribute('aria-label');
        }

        // aria-labelledby
        const labelledBy = element.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelElement = document.getElementById(labelledBy);
            if (labelElement) {
                return labelElement.textContent.trim();
            }
        }

        // Associated label
        if (element.id) {
            const label = document.querySelector(`label[for="${element.id}"]`);
            if (label) {
                return label.textContent.trim();
            }
        }

        // Enclosing label
        const enclosingLabel = element.closest('label');
        if (enclosingLabel) {
            return enclosingLabel.textContent.trim();
        }

        // Button text content
        if (element.tagName.toLowerCase() === 'button') {
            return element.textContent.trim();
        }

        // Input value or placeholder
        if (element.value && element.value.trim()) {
            return element.value.trim();
        }
        if (element.placeholder) {
            return element.placeholder;
        }

        // Link text content
        if (element.tagName.toLowerCase() === 'a') {
            return element.textContent.trim();
        }

        // Image alt text
        if (element.tagName.toLowerCase() === 'img') {
            return element.alt || '';
        }

        // Element text content
        return element.textContent.trim();
    }

    getAccessibleDescription(element) {
        // aria-describedby
        const describedBy = element.getAttribute('aria-describedby');
        if (describedBy) {
            const descElement = document.getElementById(describedBy);
            if (descElement) {
                return descElement.textContent.trim();
            }
        }

        // title attribute
        return element.title || '';
    }

    getHeadingLevel(element) {
        if (element.tagName.match(/^H[1-6]$/)) {
            return parseInt(element.tagName.charAt(1));
        }

        if (element.getAttribute('role') === 'heading') {
            return parseInt(element.getAttribute('aria-level')) || 1;
        }

        return null;
    }

    getExpandedState(element) {
        const expanded = element.getAttribute('aria-expanded');
        if (expanded === 'true') return true;
        if (expanded === 'false') return false;
        return null;
    }

    getElementBounds(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            top: Math.round(rect.top),
            left: Math.round(rect.left),
            right: Math.round(rect.right),
            bottom: Math.round(rect.bottom)
        };
    }

    generateSelector(element) {
        // Try ID first
        if (element.id) {
            return `#${element.id}`;
        }

        // Try data attributes
        for (const attr of element.attributes) {
            if (attr.name.startsWith('data-') && attr.value) {
                return `[${attr.name}="${attr.value}"]`;
            }
        }

        // Try class-based selector
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/);
            if (classes.length > 0) {
                return `.${classes[0]}`;
            }
        }

        // Fallback to tag + nth-child
        const parent = element.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children);
            const index = siblings.indexOf(element) + 1;
            return `${element.tagName.toLowerCase()}:nth-child(${index})`;
        }

        return element.tagName.toLowerCase();
    }

    getRelevantAttributes(element) {
        const relevantAttrs = {};
        const importantAttributes = [
            'id', 'class', 'role', 'aria-label', 'aria-labelledby', 'aria-describedby',
            'aria-expanded', 'aria-disabled', 'aria-required', 'aria-level',
            'alt', 'title', 'placeholder', 'type', 'href', 'src'
        ];

        for (const attr of importantAttributes) {
            const value = element.getAttribute(attr);
            if (value !== null) {
                relevantAttrs[attr] = value;
            }
        }

        return relevantAttrs;
    }

    getComputedRole(element) {
        // This would ideally use the browser's computed accessibility role
        // For now, return the role we calculate
        return this.getElementRole(element);
    }

    getAriaStates(element) {
        const states = {};
        const ariaAttributes = Array.from(element.attributes)
            .filter(attr => attr.name.startsWith('aria-'))
            .reduce((acc, attr) => {
                acc[attr.name] = attr.value;
                return acc;
            }, {});

        return ariaAttributes;
    }

    getAssociatedLabels(element) {
        const labels = [];

        // aria-labelledby
        const labelledBy = element.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelElement = document.getElementById(labelledBy);
            if (labelElement) {
                labels.push({
                    type: 'aria-labelledby',
                    text: labelElement.textContent.trim(),
                    element: this.generateSelector(labelElement)
                });
            }
        }

        // Associated label
        if (element.id) {
            const label = document.querySelector(`label[for="${element.id}"]`);
            if (label) {
                labels.push({
                    type: 'label[for]',
                    text: label.textContent.trim(),
                    element: this.generateSelector(label)
                });
            }
        }

        // Enclosing label
        const enclosingLabel = element.closest('label');
        if (enclosingLabel) {
            labels.push({
                type: 'enclosing-label',
                text: enclosingLabel.textContent.trim(),
                element: this.generateSelector(enclosingLabel)
            });
        }

        return labels;
    }

    getValidationInfo(element) {
        return {
            required: element.required || element.getAttribute('aria-required') === 'true',
            pattern: element.pattern || null,
            minLength: element.minLength || null,
            maxLength: element.maxLength || null,
            min: element.min || null,
            max: element.max || null,
            step: element.step || null,
            customValidity: element.validationMessage || null,
            valid: element.validity ? element.validity.valid : null
        };
    }
}

// Create global instance
window.accessibilityIntegration = new AccessibilityIntegration();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityIntegration;
}