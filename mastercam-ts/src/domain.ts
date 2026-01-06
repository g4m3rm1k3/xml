/**
 * Domain objects for MastercamTS
 * 
 * This module defines what a part IS.
 * It has NO imports form other project modules
 * It does NOT know about databases, XML, Express, or anyhthing else.
 * 
 * THis is the CORE of the application
 */

export class Part {
    /**
     * A manufacturing part assosiated with a machine.
     * 
     * Identity: Two parts are the "same" if name and machine match.
     * Invariant: name cannot be empty or whitespace-only
     */

    public readonly name: string;
    public rev: number;
    public readonly description: string;
    public readonly machine: string;
    public readonly partId: number | undefined;
    public readonly importDate: Date;

    constructor(name: string, rev: number, description: string, machine: string, partId?: number) {
        if (!name || !name.trim()) {
            throw new Error('Part must have a name');
        }
        if (!machine || !machine.trim()) {
            throw new Error('Part must have machine')
        }
        this.name = name.trim();
        this.rev = rev;
        this.description = description.trim();
        this.machine = machine.trim()
        this.partId = partId;
        this.importDate = new Date();
    }
    /**
     * Two Parts are equal if name and machine match.
     */
    equals(other: Part): boolean {
        return this.name === other.name && this.machine === other.machine;
    }
    /**
     * Developer-friendly string representation
     */
    toString(): string {
        return `Part(name='${this.name}', rev='${this.rev}', description='${this.description}', machine='${this.machine}', id='${this.partId}')`;
    }
}