export const tipsCategories = [
  {
    id: "sunscreen",
    title: "Sunscreen Essentials",
    icon: "☀️",
    color: "amber",
    bullets: [
      "Apply broad-spectrum SPF 30 or higher every single day, even when indoors or cloudy.",
      "Use two full finger-lengths of sunscreen for your face and neck.",
      "Reapply every 2 hours if outdoors, sweating, or after swimming.",
      "Sunscreen is the #1 anti-aging product — prevention is far easier than reversal.",
      "Apply sunscreen as the final step of your morning skincare routine, before makeup.",
    ],
    proTip: "Don't forget easily missed areas like your ears, neck, and the backs of your hands.",
  },
  {
    id: "moisturizer",
    title: "Moisturizer & Hydration",
    icon: "💧",
    color: "blue",
    bullets: [
      "Apply moisturizer while your skin is still damp from cleansing to trap hydration.",
      "Choose gel-based formulas for oily skin and cream-based formulas for dry skin.",
      "Moisturizers repair and maintain your skin's natural moisture barrier.",
      "Skipping moisturizer can cause your skin to overproduce oil to compensate.",
      "Use heavier nourishing creams at night when your skin undergoes natural repair.",
    ],
    proTip: "Look for ceramides, hyaluronic acid, and glycerin to strengthen skin hydration.",
  },
  {
    id: "serum",
    title: "Targeted Serums",
    icon: "🧪",
    color: "purple",
    bullets: [
      "Apply serums after cleansing and toning, but before heavier moisturizers.",
      "Serums contain concentrated active ingredients targeting specific skin concerns.",
      "Use Vitamin C in the morning for antioxidant protection against daily pollution.",
      "Use Niacinamide or AHA/BHA in the evening to refine texture and unclog pores.",
      "Apply 3-4 drops directly to fingertips and gently press into skin without rubbing.",
    ],
    proTip: "Introduce new active serums slowly — start 2-3 times per week before daily use.",
  },
  {
    id: "facewash",
    title: "Facewash & Cleansing",
    icon: "🧼",
    color: "green",
    bullets: [
      "Wash your face twice daily — morning and evening — with lukewarm water.",
      "Avoid harsh hot water which strips your skin of essential natural oils.",
      "Massage cleanser gently in circular motions for at least 60 seconds.",
      "Double cleanse in the evening if you wear sunscreen or makeup (oil cleanser followed by water cleanser).",
      "Pat dry with a clean micro-fiber towel — never rub or pull your skin.",
    ],
    proTip: "Choose a low pH (5.5) gentle cleanser to maintain your skin's natural acid mantle.",
  },
];

export function getAllTipLines() {
  const allLines = [];
  tipsCategories.forEach((cat) => {
    cat.bullets.forEach((bullet) => {
      allLines.push({ text: bullet, category: cat.title, icon: cat.icon });
    });
    allLines.push({ text: `Pro Tip: ${cat.proTip}`, category: cat.title, icon: cat.icon });
  });
  return allLines;
}
