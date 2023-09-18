<script>
  export const mailing_list_url = "https://docs.google.com/forms/d/e/1FAIpQLSeystecQ7WksWbkHB0z7Ke_SPvvFeEBmHQkcNgFWiuVsd4EJA/viewform?usp=sf_link";
  export const schedule_visit_url = "mailto:thisisahousegallery@gmail.com?subject=Testing out mailto!&bodyThis is only a test!";
  export const next_show_cal_event_url = "https://calendar.google.com/calendar/event?action=TEMPLATE&tmeid=MjE5aGFoczNmZGtscTA3YzQzanZqYW5nNTkgZjRiM2Q0NmZkOThlZGY1NzJlNTNjYzU5YjY3MTU5NzVlMjAyMWY2MzkzMTU0NjQyNTZlYjFiNjNhNDRlMWQ1NkBn&tmsrc=f4b3d46fd98edf572e53cc59b6715975e2021f639315464256eb1b63a44e1d56%40group.calendar.google.com";
</script>

<section class="resources">
  <h2>Keep in touch</h2>
  <section class="resources__links">
    <!--
      <a class="resources__link" href="https://instagram.com/thisisahousegallery">
        <button>Instagram</button>
      </a>
    -->
    <a class="resources__link" target="_blank" href={ next_show_cal_event_url }>
      <button>Mark your calendar</button>
    </a>
    <a class="resources__link" target="_blank" href={ mailing_list_url }>
      <button>Join the mailing list</button>
    </a>
    <a class="resources__link" href={ schedule_visit_url }>
      <button>Schedule a visit</button>
    </a>
  </section>
</section>

<style lang="scss">
  .resources {
    --main-color: white;
    --secondary-color: #222222;
  }

  .resources {
    margin: 0 var(--space-page-gutter);
    padding: var(--space-section-gap) 0;

    background: #121212;
    background: var(--main-color);;
    border-top: 1px solid var(--secondary-color);
    border-bottom: 1px solid var(--secondary-color);
    color: white;

    & h2 {
      display: none;
    }

    &__links {
      display: flex; 
      gap: var(--space-page-gutter);
    }
    &__link {
      flex: 1;

      & button {
        width: 100%;
        padding: 8px 16px;
        height: 100%;
        font-size: 12px;
        font-weight: 300;

        background: #222222;
        border: 1px solid white;
        color: white;

        &:hover {
          background: white;
          border: 1px solid #222222;
          color: #222222;
        }

        @media screen and (min-width: 768px) {
          padding: 32px;
          font-size: 18px;
          font-weight: 400;
        }
      }
    }
  }
</style>
