// I'm a fucking image processor bitch
import image_database_raw from "../data/image-database-06_12_2024-v1.json";

// make a deep copy
let image_db = JSON.parse(JSON.stringify( image_database_raw ));

// cuz were using trphy
image_db = image_db["@graph"];

// process all images via vite glob
const processed_images = import.meta.glob( "/src/media/exhibition-images/*", { 
  query: { format: "webp;avif;jpg", w: "200;400;600;1200", picture: "" },
  import: 'default',
  // eager: true
});

// attach those to image_db
// ...without eager is just path?
/*
image_db.forEach( async ( item ) => {
  item.srcset = await processed_images[ `../media/exhibition-images/${ item.photo[0].filename }` ]();
});
*/
/*
image_db.forEach(( item ) => {
  item.srcset = processed_images[ `../media/exhibition-images/${ item.photo[0].filename }` ];
});
*/
// = turns out I can't pre-process any of this shit?! FUCK YOU ASTRO
// > WHY MAKE ME PROCESS THE IMAGES ON EVERY FUCKING PAGE
// > WTF

export function testMe() {
  console.log( image_db[0] );
}

export function get_image_path( filename ) {
  return `/src/media/exhibition-images/${ filename }`;
}

export function getProcessedImages() {
  return processed_images;
}

export function getTestImagePath() {
  return get_image_path( image_db[0].photo[0].filename );
}

