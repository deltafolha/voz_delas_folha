import { isMobile } from 'react-device-detect';
export default function Loading () {
    return (
        <section className={isMobile ? "min-h-screen min-w-full bg-gray-100 flex" : "min-h-screen p-20 bg-gray-100 flex"}>
            <div className="mx-auto my-auto animate-spin ease-linear h-20 w-20 rounded-full border-4 border-l-gray-198 border-r-gray-200 border-b-gray-200 border-t-cyan-500"></div>
        </section>
    )
}