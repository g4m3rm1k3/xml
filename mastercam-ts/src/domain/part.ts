/**
 * src/domain/part.ts
 * 
 * The Part domain entity - a manufacturing file associated with a machine
 * 
 * INVARIANTS:
 * - A Part MUST hav a non-empty name
 * - A Part's name cannot be "Unknown" (hides data problems)
 */

// ===========================================================
// TYPE DEFINITIONS
// ===========================================================

/**
 * The data needed to create a Part.
 * This is what external code provides.
 */
export interface PartInput {
    name: string;
    machine?: string; // Optional - the ? means int can be undefined
}

/**
 * The complete Part entity after construction.
 * This is what the domain guarantees.
 */
export interface Part {
    readonly name: string;
    readonly machine: string | undefined;
    readonly importDate: Date;
}

// ===========================================================
// FACTORY FUNCTION
// ===========================================================

/**
 * Creates a validated Part.
 * 
 * This is a factory function, not a class constructor, Why?
 * - In functional TypeScript, we often prefere functions over classes
 * - Factory functions can return different types (success/failure)
 * - Easier to test and compose
 * 
 * @param input - The data to create a Part from
 * @reutrns A validated Part object
 * @throws Error if invariants are violated
 */
export function createPart(input: PartInput): Part {
    // INVARIANT: name must not be empty
    if (!input.name || input.name.trim() === '') {
        throw new Error('Part name is required');
    }
    // INVARIANT: name cannot be "unkonown"
    if (input.name.toLowerCase() === 'unknown') {
        throw new Error('Part name cannot be "unknown"');
    }

    // Construct the Part with all required fields
    return {
        name: input.name.trim(),
        machine: input.machine?.trim(), // Optinoal chaining: undefined if machine is undefined
        importDate: new Date(),
    }
}