import { slugify } from "../utils/basic-javascript.js";
import artwork_database from "../data/artwork-database.json";
import { get_artwork_images } from "../utils/image-db-handler.js";

export function get_artists_work( artist ) {
  return artwork_database.filter( item => {
    return item["Artist"] == artist;
  })
}

export function get_artists_work_with_images( artist ) {
  let artwork_list = artwork_database.filter( item => {
    return item["Artist"] == artist;
  });

  artwork_list.forEach( item => {
    item["Images"] = get_artwork_images( item["Title"] );
  });

  return artwork_list;
}

export function get_artwork_data( title_slug ) {
    return  artwork_database.filter( item => {
      return slugify(item["Tile"]) == title_slug;
    })
}
