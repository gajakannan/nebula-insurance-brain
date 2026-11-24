import { ContractError } from './runtime.mjs';

const RECIPE_KEYS = ['prefix', 'character', 'suffix', 'count'];
const REPEAT_CHARACTERS = new Set(['x', '[', ']', '{', '}']);
const MAX_REPEAT = 16_777_217;

/** Expand compact reviewed fixtures without embedding megabytes in the inventory. */
export function rawForCase(entry) {
  const invalid = () => { throw new ContractError('CONTRACT_CASE_INVENTORY_INVALID'); };
  if (entry === null || typeof entry !== 'object' || Array.isArray(entry) || entry.kind !== 'raw-json') invalid();
  const raw = Object.hasOwn(entry, 'raw');
  const repeated = Object.hasOwn(entry, 'raw_repeat');
  if (raw === repeated) invalid();
  if (raw) {
    if (typeof entry.raw !== 'string') invalid();
    return entry.raw;
  }
  const recipe = entry.raw_repeat;
  if (recipe === null || typeof recipe !== 'object' || Array.isArray(recipe)
      || Object.keys(recipe).length !== RECIPE_KEYS.length
      || RECIPE_KEYS.some((key) => !Object.hasOwn(recipe, key))
      || typeof recipe.prefix !== 'string' || typeof recipe.suffix !== 'string'
      || typeof recipe.character !== 'string' || recipe.character.length !== 1
      || !REPEAT_CHARACTERS.has(recipe.character)
      || !Number.isInteger(recipe.count) || recipe.count < 0 || recipe.count > MAX_REPEAT) invalid();
  return recipe.prefix + recipe.character.repeat(recipe.count) + recipe.suffix;
}
