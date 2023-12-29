import artwork_database from "../data/artwork-database-dec_25_2023-v2.json";
import artist_database from "../data/artist-database-12_28_2023-v2.json";
import * as image_db from "../utils/image-db-handler.js";
import { slugify } from "../utils/basic-javascript.js";

export function get_all_artists() {
  return artist_database;
};

export function get_all_artwork() {
  return artwork_database.filter( item => {
    return ( item.Published == "TRUE" );
  })
};

// Modify db for easy-access keys
// > Attach cover image
get_all_artwork().forEach( item => {
  item.Cover = image_db.get_artwork_cover( item["ID"] );
});

export function get_artists_work( artist ) {
  return artwork_database.filter( item => {
    return item["Artist"] == artist;
  })
}

export function get_artists_work_with_images( artist ) {
  let artwork_list = get_all_artwork().filter( item => {
    return item["Artist"] == artist;
  });

  artwork_list.forEach( item => {
    item["Images"] = image_db.get_artwork_images( item["ID"] );
  });

  return artwork_list;
}

export function get_artwork_data( id ) {
    return artwork_database.filter( item => {
      return item["ID"] == id;
    })
}
