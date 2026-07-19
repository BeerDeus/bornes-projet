// Icônes SVG inline, style trait fin (~Feather) - évite d'ajouter une
// dépendance externe (lucide-react etc.) juste pour une poignée de pictos
// (4 modules + chevron + soleil/lune).
function Trait({ children, className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function IconBowling({ className }) {
  return (
    <Trait className={className}>
      <path d="M12 3v3.2" />
      <circle cx="10.6" cy="5" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="13.4" cy="5" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="12" cy="15.5" r="5.3" />
    </Trait>
  );
}

export function IconBar({ className }) {
  return (
    <Trait className={className}>
      <path d="M5 4h14l-6 7.5V19" />
      <path d="M9 19h6" />
      <path d="M5.6 4.9l3.3 4.2" />
    </Trait>
  );
}

export function IconKaraoke({ className }) {
  return (
    <Trait className={className}>
      <rect x="9" y="2.5" width="6" height="10" rx="3" />
      <path d="M6 11a6 6 0 0 0 12 0" />
      <path d="M12 17v4" />
      <path d="M8.5 21h7" />
    </Trait>
  );
}

export function IconQuiz({ className }) {
  return (
    <Trait className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.6 9.4a2.4 2.4 0 1 1 3.3 2.2c-0.9 0.4-1.1 1-1.1 1.9" />
      <circle cx="12" cy="16.3" r="0.7" fill="currentColor" stroke="none" />
    </Trait>
  );
}

export function IconChevron({ className }) {
  return (
    <Trait className={className}>
      <path d="M9 6l6 6-6 6" />
    </Trait>
  );
}

export function IconSun({ className }) {
  return (
    <Trait className={className}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2.2M12 19.3v2.2M4.2 12H2M22 12h-2.2M5.3 5.3l1.5 1.5M17.2 17.2l1.5 1.5M5.3 18.7l1.5-1.5M17.2 6.8l1.5-1.5" />
    </Trait>
  );
}

export function IconMoon({ className }) {
  return (
    <Trait className={className}>
      <path d="M20.5 14.7A8.5 8.5 0 1 1 9.3 3.5a7 7 0 0 0 11.2 11.2z" />
    </Trait>
  );
}

export function IconActivity({ className }) {
  return (
    <Trait className={className}>
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </Trait>
  );
}

export function IconPlus({ className }) {
  return (
    <Trait className={className}>
      <path d="M12 5v14M5 12h14" />
    </Trait>
  );
}

export function IconTrash({ className }) {
  return (
    <Trait className={className}>
      <path d="M4 7h16" />
      <path d="M9 7V4.5A1.5 1.5 0 0 1 10.5 3h3A1.5 1.5 0 0 1 15 4.5V7" />
      <path d="M6 7l1 13.5A1.5 1.5 0 0 0 8.5 22h7a1.5 1.5 0 0 0 1.5-1.5L18 7" />
    </Trait>
  );
}

export function IconPencil({ className }) {
  return (
    <Trait className={className}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" />
    </Trait>
  );
}
