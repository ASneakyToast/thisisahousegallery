import image_database from "../data/image-database-oct_16_2023.json";
import artwork_database from "../data/artwork-database.json";

export function get_artwork_images( artwork ) {
  return image_database["@graph"].filter( item => {
    return item.tag.includes( artwork );
  });
}
