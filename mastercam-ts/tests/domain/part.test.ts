/**
 * test/domain/part.test.ts
 * 
 * Unit test for hte Part domain entity
 * Test are written BEFORE implementation (TDD).
 */

import { describe, it, expect } from 'vitest';
import { createPart, Part } from '../../src/domain/part.js'

// ===========================================================
// HAPPY PATH TESTS
// ===========================================================


describe('Part', () => {
    describe('createPart', () => {
        it('creates a Part with required name', () => {
            //Arrange
            const input = { name: 'widget-housing' };

            //Act
            const part = createPart(input)

            //Assert
            expect(part.name).toBe('widget-housing');
            expect(part.machine).toBeUndefined();
            expect(part.importDate).toBeInstanceOf(Date);
        });
        it('creats a Part with name and machine', () => {
            // Arrang
            const input = { name: 'bracket', machine: 'Haas VF-2' };

            // Act
            const part = createPart(input);

            //Assert
            expect(part.name).toBe('bracket');
            expect(part.machine).toBe('Haas VF-2');
        });

        it('trims whitespace from machine', () => {
            const part = createPart({ name: 'part', machine: '   Mazak   ' });
            expect(part.machine).toBe('Mazak');
        })
    })
})
