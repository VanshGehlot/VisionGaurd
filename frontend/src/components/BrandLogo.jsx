import logoPng from "../assets/visionguard-logo.png";

const sizeClass = {
  sm: "brand-logo--sm",
  md: "brand-logo--md",
  lg: "brand-logo--lg",
};

export default function BrandLogo({
  variant = "horizontal",
  size = "md",
  subtitle,
  className = "",
}) {
  const resolvedVariant = ["icon", "wordmark", "horizontal"].includes(variant) ? variant : "horizontal";
  const showSubtitle = resolvedVariant !== "icon" && subtitle;

  return (
    <span className={`brand-logo brand-logo--${resolvedVariant} ${sizeClass[size] || sizeClass.md} ${className}`}>
      <img className="brand-logo__image" src={logoPng} alt="VisionGuard" />
      {showSubtitle ? (
        <span className="brand-logo__copy">
          <span className="brand-logo__subtitle">{subtitle}</span>
        </span>
      ) : null}
    </span>
  );
}
