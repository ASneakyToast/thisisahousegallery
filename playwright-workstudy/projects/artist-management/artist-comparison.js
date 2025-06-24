/**
 * Artist Data Comparison Utilities
 * 
 * Provides functions to compare artist data between test configuration
 * and CMS data to determine what changes need to be made.
 */

/**
 * Compare two artist objects and return differences
 * @param {Object} testData - Artist data from test configuration
 * @param {Object} cmsData - Artist data from CMS
 * @returns {Object} Comparison result with differences
 */
export function compareArtistData(testData, cmsData) {
  const differences = {};
  const fieldsToCompare = ['name', 'bio', 'website', 'birth_year'];
  
  let hasChanges = false;
  
  for (const field of fieldsToCompare) {
    const testValue = normalizeValue(testData[field]);
    const cmsValue = normalizeValue(cmsData[field]);
    
    if (testValue !== cmsValue) {
      differences[field] = {
        test: testValue,
        cms: cmsValue,
        changed: true
      };
      hasChanges = true;
    } else {
      differences[field] = {
        test: testValue,
        cms: cmsValue,
        changed: false
      };
    }
  }
  
  return {
    hasChanges,
    differences,
    changedFields: Object.keys(differences).filter(key => differences[key].changed)
  };
}

/**
 * Normalize values for comparison
 * @param {any} value - Value to normalize
 * @returns {string|null} Normalized value
 */
function normalizeValue(value) {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  
  if (typeof value === 'number') {
    return value.toString();
  }
  
  if (typeof value === 'string') {
    return value.trim();
  }
  
  return String(value);
}

/**
 * Generate a human-readable summary of changes
 * @param {Object} comparison - Result from compareArtistData
 * @param {string} artistName - Name of the artist
 * @returns {string} Human-readable summary
 */
export function generateChangeSummary(comparison, artistName) {
  if (!comparison.hasChanges) {
    return `✅ No changes needed for "${artistName}"`;
  }
  
  const changes = comparison.changedFields.map(field => {
    const diff = comparison.differences[field];
    const testVal = diff.test || '(empty)';
    const cmsVal = diff.cms || '(empty)';
    return `  • ${field}: "${cmsVal}" → "${testVal}"`;
  });
  
  return `🔄 Changes needed for "${artistName}":\n${changes.join('\n')}`;
}

/**
 * Validate that required fields are present in test data
 * @param {Object} testData - Artist data from test configuration
 * @returns {Object} Validation result
 */
export function validateArtistData(testData) {
  const errors = [];
  const warnings = [];
  
  // Required fields
  if (!testData.name || testData.name.trim() === '') {
    errors.push('Name is required');
  }
  
  if (!testData.id || testData.id.trim() === '') {
    errors.push('ID is required');
  }
  
  // Optional field validations
  if (testData.website && !isValidUrl(testData.website)) {
    warnings.push('Website appears to be invalid URL');
  }
  
  if (testData.birth_year && (testData.birth_year < 1000 || testData.birth_year > 2100)) {
    warnings.push('Birth year seems unusual');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}

/**
 * Simple URL validation
 * @param {string} url - URL to validate
 * @returns {boolean} True if URL appears valid
 */
function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Extract comparable data from CMS form
 * @param {Object} page - Playwright page object
 * @returns {Object} Extracted artist data
 */
export async function extractCMSArtistData(page) {
  const artistData = {};
  
  try {
    // Extract name
    const nameField = page.locator('input[name="name"], #id_name');
    if (await nameField.count() > 0) {
      artistData.name = await nameField.inputValue();
    }
    
    // Extract bio
    const bioField = page.locator('textarea[name="bio"], #id_bio');
    if (await bioField.count() > 0) {
      artistData.bio = await bioField.inputValue();
    }
    
    // Extract website
    const websiteField = page.locator('input[name="website"], #id_website');
    if (await websiteField.count() > 0) {
      artistData.website = await websiteField.inputValue();
    }
    
    // Extract birth year
    const birthYearField = page.locator('input[name="birth_year"], #id_birth_year');
    if (await birthYearField.count() > 0) {
      const birthYearValue = await birthYearField.inputValue();
      artistData.birth_year = birthYearValue ? parseInt(birthYearValue) : null;
    }
    
    return artistData;
  } catch (error) {
    console.warn(`Error extracting CMS artist data: ${error.message}`);
    return {};
  }
}

/**
 * Check if two artists are the same person (by name)
 * @param {Object} testData - Artist data from test configuration
 * @param {Object} cmsData - Artist data from CMS
 * @returns {boolean} True if they appear to be the same artist
 */
export function isSameArtist(testData, cmsData) {
  const testName = normalizeValue(testData.name);
  const cmsName = normalizeValue(cmsData.name);
  
  if (!testName || !cmsName) {
    return false;
  }
  
  // Exact match
  if (testName.toLowerCase() === cmsName.toLowerCase()) {
    return true;
  }
  
  // Close match (handles minor differences)
  const similarity = calculateSimilarity(testName.toLowerCase(), cmsName.toLowerCase());
  return similarity > 0.9;
}

/**
 * Calculate similarity between two strings
 * @param {string} str1 - First string
 * @param {string} str2 - Second string  
 * @returns {number} Similarity score between 0 and 1
 */
function calculateSimilarity(str1, str2) {
  if (str1 === str2) return 1;
  
  const maxLength = Math.max(str1.length, str2.length);
  if (maxLength === 0) return 1;
  
  const editDistance = levenshteinDistance(str1, str2);
  return (maxLength - editDistance) / maxLength;
}

/**
 * Calculate Levenshtein distance between two strings
 * @param {string} str1 - First string
 * @param {string} str2 - Second string
 * @returns {number} Edit distance
 */
function levenshteinDistance(str1, str2) {
  const matrix = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
}