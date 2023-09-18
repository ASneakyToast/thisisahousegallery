<section class="exhibitions__cards">
  <article class="exhibitions__card pathway-card__last" >
    <img src="exhibitions/thisisalivingroom/Showcard001.jpg" />
  </article>
  <article class="exhibitions__card pathway-card__next">
    <img src="exhibitions/thisisalivingroom/Showcard001.jpg" />
  </article>
  <article class="exhibitions__card pathway-card__your">
    <img src="exhibitions/thisisalivingroom/Showcard001.jpg" />
  </article>
</section>

<style lang="scss">
  .exhibitions {
    padding: 80px 140px;
    display: flex;
    flex-direction: row;
    gap: 40px;

    &__interface {
      flex: 2;

      & h2 {
        margin: 0 0 40px;
      }
    }

    &__critical-pathways {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 24px;
      font-size: 24px;

      & a {
        width: fit-content;
      }
    }

    &__pathway {
      display: inline-block;
    }
    &__pathway:hover {
      text-decoration: underline;
    }

    &__cards {
      flex: 3;
      position: relative;

      min-height: 500px;
    }

    &__card {
      transition: all 1s;
      transition-timing-function: ease-in-out;

      & img {
        max-width: 300px;
        max-height: 300px;
      }
    }

    &__card--active {
      transform: none !important;
      bottom: 200px !important;
      left: 200px !important;
    }

    &__card:nth-child(1) {
      position: absolute;
      left: 20%; bottom: -80px;
      transform: rotate3d(21, 4, -6, -283deg);
      z-index: 1;
    }
    &__card:nth-child(2) {
      position: absolute;
      left: 45%; bottom: -85px;
      transform: rotate3d(143,4,-6,-285deg);
      z-index: 3;
    }
    &__card:nth-child(3) {
      position: absolute;
      left: 70%; bottom: -80px;
      transform: rotate3d(19, -3, 5, 75deg);
      z-index: 2;
    }
  }
</style>
