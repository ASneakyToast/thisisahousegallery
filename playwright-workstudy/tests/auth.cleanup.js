import { test as cleanup } from '@playwright/test';
import fs from 'fs-extra';
import { Environment } from '../config/environment.js';

cleanup('remove auth file', async ({}) => {
  try {
    await fs.remove(Environment.paths.auth);
    console.log('🧹 Authentication file cleaned up');
  } catch (error) {
    console.log('ℹ️  No auth file to clean up');
  }
});