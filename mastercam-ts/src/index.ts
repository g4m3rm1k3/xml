/**
 * src/index.ts
 * 
 * Application entry point
 * For now, jsut a simple demonstration.
 */
import { createPart } from './domain/part.js';

// Create a sample part
const part = createPart({
    name: 'widget-housing',
    machine: 'Haas VF-2',
});

console.log("Created Part:");
console.log(`   Name: ${part.name}`)
console.log(`   Machine: ${part.machine ?? 'Not specified'}`);
console.log(`   Imported: ${part.importDate.toISOString()}`)

// Demonstrate invariant enforcement
try {
    createPart({ name: '' });
} catch (error) {
    if (error instanceof Error) {
        console.log(`\nInvariant enfroced: ${error.message}`);
    }
}
