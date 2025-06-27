import { chromium } from 'playwright';

const artworks = [
  {
    title: "Untitled pulp sheet #6",
    date: "2023-01-01",
    size: "45 x 36 x 34",
    materials: ["Pulp"]
  },
  {
    title: "Mountain #1", 
    date: "2023-01-01",
    size: "7 1/4 x 7 1/4 x 1 1/2",
    materials: ["Printmedia"]
  },
  {
    title: "Ad hoc lamp",
    date: "2023-01-01", 
    size: "26 x 62 1/2 x 28",
    materials: ["Sculpture"]
  },
  {
    title: "Mountain #2",
    date: "2023-01-01",
    size: "7 1/4 x 5 1/2 x 1 3/4", 
    materials: ["Printmedia"]
  },
  {
    title: "Pulp Dump #1",
    date: "2023-01-01",
    size: "37 x 37 x 1 3/4",
    materials: ["Pulp"]
  },
  {
    title: "Lost in Translation",
    date: "2019-01-01",
    size: "17\" x 10",
    materials: ["Screenprint"]
  }
];

const artist = {
  name: "Joel Lithgow"
};

async function addArtworks() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to login page
    await page.goto('https://housegallery-dev-jrl-service-591747915969.us-west2.run.app/admin/login/');
    
    // Fill in login credentials
    await page.fill('input[name="username"]', 'playwright-workstudy');
    await page.fill('input[name="password"]', 'catdogcatdog');
    await page.click('button[type="submit"]');
    
    // Wait for login to complete
    await page.waitForURL('**/admin/**');
    
    console.log('✅ Successfully logged in');
    
    // Navigate to artworks page
    await page.goto('https://housegallery-dev-jrl-service-591747915969.us-west2.run.app/admin/snippets/artworks/artwork/');
    
    let successCount = 0;
    let skipCount = 0;
    
    for (const artwork of artworks) {
      try {
        console.log(`\n🎨 Processing artwork: ${artwork.title}`);
        
        // Check if artwork already exists by looking for it in the list
        const existingArtwork = await page.locator(`text="${artwork.title}"`).count();
        if (existingArtwork > 0) {
          console.log(`⏭️  Artwork already exists, skipping: ${artwork.title}`);
          skipCount++;
          continue;
        }
        
        // Click Add Artwork
        await page.click('a[href*="/add/"]');
        
        // Fill in title
        await page.fill('input[name="title"]', artwork.title);
        
        // Select artist (Joel Lithgow)
        await page.click('button:has-text("Choose Artist")');
        await page.waitForSelector('text="Joel Lithgow"', { timeout: 5000 });
        await page.click('a:has-text("Joel Lithgow")');
        
        // Fill in date - handle the date picker carefully
        const dateInput = page.locator('input[name="date"]');
        await dateInput.click();
        await dateInput.fill(artwork.date.split('-')[0]); // Just the year
        
        // Close date picker by clicking elsewhere on the form
        await page.click('input[name="title"]');
        await page.waitForTimeout(500);
        
        // Fill in size
        await page.fill('input[name="size"]', artwork.size);
        
        // Fill in materials/tags - handle the tag widget properly
        const tagsInput = page.locator('input[name="materials"]').first();
        await tagsInput.scrollIntoViewIfNeeded();
        await tagsInput.click();
        await tagsInput.type(artwork.materials[0]);
        await page.keyboard.press('Enter'); // Confirm the tag entry
        await page.waitForTimeout(500);
        
        // Save the artwork
        await page.click('button:has-text("Save")');
        
        // Wait for success and return to list
        await page.waitForSelector('text=created', { timeout: 10000 });
        
        console.log(`✅ Successfully added: ${artwork.title}`);
        successCount++;
        
        // Navigate back to artworks list for next iteration
        await page.goto('https://housegallery-dev-jrl-service-591747915969.us-west2.run.app/admin/snippets/artworks/artwork/');
        await page.waitForTimeout(1000);
        
      } catch (error) {
        console.error(`❌ Failed to add "${artwork.title}": ${error.message}`);
        
        // Navigate back to artworks list to continue with next artwork
        try {
          await page.goto('https://housegallery-dev-jrl-service-591747915969.us-west2.run.app/admin/snippets/artworks/artwork/');
          await page.waitForTimeout(500);
        } catch (navError) {
          console.error(`Failed to navigate back to artwork list: ${navError.message}`);
        }
      }
    }
    
    console.log(`\n🎉 Batch complete!`);
    console.log(`✅ Successfully added: ${successCount} artworks`);
    console.log(`⏭️  Skipped (already exist): ${skipCount} artworks`);
    console.log(`❌ Failed: ${artworks.length - successCount - skipCount} artworks`);
    
  } catch (error) {
    console.error('❌ Critical error:', error);
  } finally {
    await browser.close();
  }
}

addArtworks();