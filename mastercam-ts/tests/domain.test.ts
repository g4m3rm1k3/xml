/**
 * Tests for domain objects. Written BEFORE the code.
 */
import { describe, it, expect } from 'vitest';
import { Part } from '../src/domain.js'

describe('Part', () => {
    it('requires a name', () => {
        expect(() => new Part('', 5, 'desc', 'DV12')).toThrow('Part must have a name');
    });
    it('stores attributes', () => {
        const part = new Part('4800123', 5, 'desc', 'OM05');

        expect(part.name).toBe('4800123');
        expect(part.machine).toBe('OM05')
    });
    it('machine is required', () => {
        expect(() => new Part('4800274', 5, 'desc', '')).toThrow("Part must have machine")
    });
    it('trims whitespace from name', () => {
        const part = new Part(' 4801234 ', 5, 'desc', 'M11');
        expect(part.name).toBe('4801234')
    });
    it('two partrs with same name and machine are equal', () => {
        const part1 = new Part('a', 5, 'desc', '5');
        const part2 = new Part('a', 5, 'desc', '5');

        expect(part1.equals(part2)).toBe(true);
    });
    it('two parts with different machines are not equal', () => {
        const part1 = new Part('a', 5, 'desc', '5');
        const part2 = new Part('a', 5, 'desc', '4');

        expect(part1.equals(part2)).toBe(false);
    })

});