export default function ChartContainer (props) {
    return (
        <div className="flex flex-wrap w-8/12 border-1 mx-auto mb-10 border-b-4 border-gray-300 pb-10">
            <h1 className="text-xs p-2 border-cyan-500 border-b-4 border-l-4 mb-4">{props.title}</h1>
            {props.child}
        </div>
    )
}