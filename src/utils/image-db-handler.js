import image_database from "../data/image-database-nov_4_2023-v7.json";
import artwork_database from "../data/artwork-database-nov_04_2023.json";

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
