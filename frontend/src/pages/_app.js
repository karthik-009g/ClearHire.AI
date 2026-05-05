import { useEffect, useRef } from "react";
import "../styles/globals.css";

export default function App({ Component, pageProps }) {
  const cursorOuterRef = useRef(null);
  const cursorInnerRef = useRef(null);

  useEffect(() => {
    const curO = cursorOuterRef.current;
    const curI = cursorInnerRef.current;
    if (!curO || !curI) {
      return undefined;
    }

    let mx = 0;
    let my = 0;
    let ox = 0;
    let oy = 0;
    let frameId = 0;

    const animate = () => {
      ox += (mx - ox) * 0.13;
      oy += (my - oy) * 0.13;
      curI.style.left = `${mx}px`;
      curI.style.top = `${my}px`;
      curO.style.left = `${ox}px`;
      curO.style.top = `${oy}px`;
      frameId = window.requestAnimationFrame(animate);
    };

    const onMove = (event) => {
      mx = event.clientX;
      my = event.clientY;
    };

    const isHoverTarget = (target) => target instanceof Element && target.matches("button, input, a, [data-hover]");

    const onMouseOver = (event) => {
      if (isHoverTarget(event.target)) {
        curO.style.width = "52px";
        curO.style.height = "52px";
      }
    };

    const onMouseOut = (event) => {
      if (isHoverTarget(event.target)) {
        curO.style.width = "38px";
        curO.style.height = "38px";
      }
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseover", onMouseOver);
    document.addEventListener("mouseout", onMouseOut);
    animate();

    return () => {
      window.cancelAnimationFrame(frameId);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseover", onMouseOver);
      document.removeEventListener("mouseout", onMouseOut);
    };
  }, []);

  return (
    <>
      <div id="cur" aria-hidden="true">
        <div id="cur-o" ref={cursorOuterRef} />
        <div id="cur-i" ref={cursorInnerRef} />
      </div>
      <Component {...pageProps} />
    </>
  );
}
