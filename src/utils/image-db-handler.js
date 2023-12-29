import image_database from "../data/image-database-dec_28_2023.json";
import artwork_database from "../data/artwork-database-dec_25_2023-v2.json";

/* The before before */
/*
export function get_all_images() {
  return image_database["@graph"];
}

export function get_exhibition_images( exhibition ) {
  return image_database["@graph"].filter( item => {
    return item.tag.includes( exhibition );
  });
}

export function get_artwork_images( artwork_id ) {
  return image_database["@graph"].filter( item => {
    return item["InstanceID"] == artwork_id;
  });
}

export function get_artwork_cover( artwork_id ) {
  let cover = get_artwork_images( artwork_id ).find( image => {
    return image.tag.includes( "Cover" );
  });
  return cover;
}
*/

/* now here the sauce */
/* ...hopefully... */ 
/* ...nope........ */

export function get_image_path( title ) {
  return `/src/media/exhibition-images/${ title }`;
}

export function get_all_images() {
  return image_database["@graph"];
}

// Process images for all to use
// > process all images
const processed_images = import.meta.glob( "../media/exhibition-images/*", { 
  query: { format: "webp;avif;jpg", w: "200;400;600;1200", picture: "" },
  import: 'default'
});

/* why did I create a var for this */
/*
let all_image_data = get_all_images();
all_image_data.forEach( async ( item, index ) => {
  //TODO: change this to use get_image_path function
  
  // > attach srcset to image data
  let srcset = await processed_images[ `../media/exhibition-images/${ item.photo[0].filename }` ]();
  all_image_data[ index ].srcset = srcset;
});
*/

// > attach processed file to image data
get_all_images().forEach( async ( item ) => {
  item.srcset = await processed_images[ `../media/exhibition-images/${ item.photo[0].filename }` ]();
});

export function get_exhibition_images( exhibition ) {
  return get_all_images().filter( item => {
    return item.tag.includes( exhibition );
  });
}

export function get_artwork_images( artwork_id ) {
  return get_all_images().filter( item => {
    return item["InstanceID"] == artwork_id;
  });
}

/*
export function get_artwork_images( artwork_id ) {
  // find related images
  let images_with_id = image_database["@graph"].filter( item => {
    return item["InstanceID"] == artwork_id;
  });

  // add processed image paths
  // ...shouldn't need to do this if I process them all at start
  images_with_id.forEach( async ( item ) => {
    item.processed = await processed_images[ get_image_path( item.photo[0].filename ) ]();
  });

  return images_with_id;
}
*/

export function get_artwork_cover( artwork_id ) {
  let cover = get_artwork_images( artwork_id ).find( image => {
    return image.tag.includes( "Cover" );
  });
  return cover;
}
