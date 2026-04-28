# components/CinematicHero.tsx
export default function CinematicHero({ resort }: any) {
  return (
    <section className="relative h-screen overflow-hidden bg-black">
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      >
        <source src={resort.hero_video} type="video/mp4" />
      </video>
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
      <div className="relative z-10 h-full flex flex-col justify-end pb-20 px-8 md:px-16 text-white">
        <h1 className="text-display-lg font-serif">{resort.name}</h1>
        <p className="text-body-lg mt-4 max-w-xl">{resort.tagline}</p>
        <button className="mt-8 bg-white text-black px-8 py-4 rounded-full font-medium text-lg">
          Begin Your Journey
        </button>
      </div>
    </section>
  );
}
