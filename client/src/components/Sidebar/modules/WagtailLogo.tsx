import React from 'react';

interface WagtailLogoProps {
  className?: string;
  slim: boolean;
}

const WagtailLogo = ({ className, slim }: WagtailLogoProps) => {
  const feathersClasses =
    'group-hover:w-text-black w-transition-all w-duration-150';

  return (
    <svg
      style={{
        left: slim ? '-1.125rem' : '-1.75rem',
      }}
      className={`
         sidebar-wagtail-branding__icon
         !w-overflow-visible
         w-group
         w-text-surface-menus
         w-z-10
         w-absolute
         w-transition-all
         w-duration-150
         hover:w-scale-[0.85]
         hover:w-rotate-[5deg]
         ${className || ''}
         ${
           slim
             ? 'w-w-[58px] w-h-[57px] w-top-2 hover:w-translate-x-1 hover:-w-translate-y-1'
             : 'w-w-[120px] w-h-[200px] -w-top-1  hover:w-translate-x-2 hover:-w-translate-y-3'
         }
      `}
      width="225"
      height="274"
      viewBox="0 0 225 274"
      enableBackground="new 0 0 225 274"
      xmlSpace="preserve"
      aria-hidden="true"
    >
      <g>
        <path
          className="wagtail-logo-face"
          fill="#FFF"
          d="M194.897 79.492c-8.392-12.793-22.602-21.27-38.773-21.27-5.322 0-10.496.915-15.32 2.62a30.755 30.755 0 0 1-4.039-15.3c0-17.078
          13.325-30.792 29.918-30.792 4.274 0 8.046.776 11.565 2.328 1.746-2.566 3.491-5.64 5.236-9.476 7.108 4.095 19.786 14.99 21.26
          33.397L190.72 61.88l4.177 17.612Z"
        />
        <path
          className={`w-hidden ${feathersClasses}`}
          data-part="eye--closed"
          d="M183.083 36.4189C181.131 37.0166 179.364 38.6306 178.317 40.5186C178.048 41.0035 177.464 41.2495 176.954 41.0359L173.968
          39.7874C173.46 39.5751 173.217 38.9905 173.464 38.498C175.023 35.3889 177.903 32.5075 181.558 31.388C185.602 30.1494 190.075
          31.2163 194.019 35.3681C194.398 35.7669 194.352 36.3991 193.936 36.7609L191.492 38.8897C191.073 39.2538 190.441 39.2043 190.053
          38.8094C187.354 36.0624 184.921 35.8559 183.083 36.4189Z"
          fill="currentColor"
        />
        <path
          className={feathersClasses}
          data-part="eye--open"
          fill="currentColor"
          d="M185.54 42.697c3.332 0 6.034-2.781 6.034-6.211s-2.702-6.21-6.034-6.21c-3.333 0-6.034 2.78-6.034 6.21s2.701 6.21 6.034 6.21Z"
        />
        <path
          className={feathersClasses}
          data-part="body"
          fill="currentColor"
          d="m21.867 193.558 92.839-164.565C122.124 11.853 138.827 0 158.135 0c9.302 0 18.102 2.588 25.393 7.504-1.76 3.882-3.52 6.987-5.28
          9.575-3.52-1.553-7.291-2.33-11.565-2.33-16.594 0-29.919 13.716-29.919 30.794 0 5.646 1.496 10.83 4.04 15.3a45.95 45.95 0 0 1
          15.319-2.62c25.896 0 46.764 21.736 46.764 48.131 0 1.104-.183 2.209-.394 3.475l-.109.665h.252c-.126.906-.315 1.811-.503
          2.717-.189.906-.377 1.811-.503 2.717v.259c-17.487 91.789-126.812 89.821-143.747 89.031l.112-.386-1.743-30.679-6.872 12.197-27.513 7.208Z"
        />

        <path
          className={feathersClasses}
          data-part="body-tail-connector"
          fill="currentColor"
          d="m49.277 186.425 8.718 18.407-1.743-30.679-6.975 12.272Z"
        />
        <path
          className={feathersClasses}
          data-part="beak"
          fill="currentColor"
          d="m204.648 41.144-11.817 18.114h31.93l-20.113-18.114Z"
        />
        <path
          data-part="feather-accent"
          fill="#FFF"
          d="m99.304 170.528-2.012 1.552s66.877-11.127 77.437-67.797l-10.56 3.623s-2.765 43.99-64.865 62.622Z"
        />
      </g>
      <path
        className={feathersClasses}
        data-part="tail"
        fill="currentColor"
        d="M56.252 174.153.456 273.202l41.847-14.025 15.692-54.345-1.743-30.679Z"
      />
    </svg>
  );
};

export default WagtailLogo;
