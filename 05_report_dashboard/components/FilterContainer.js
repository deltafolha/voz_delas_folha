import ChartDateFilter from "./ChartDateFilter";
import ChartChannelFilter from "./ChartChannelFilter";
import ChartAuthorFilter from "./ChartAuthorFilter";

export default function FilterContainer (props) {
    return (
        <div className="flex flex-wrap w-8/12 border-1 mx-auto mb-10 border-b-4 border-gray-300 pb-8">
            <ChartDateFilter dateRange={props.dateRange} setDateRange={props.setDateRange}/>
            <ChartChannelFilter selectedChannel={props.selectedChannel} setSelectedChannel={props.setSelectedChannel}/>
            <ChartAuthorFilter selectedAuthor={props.selectedAuthor} setSelectedAuthor={props.setSelectedAuthor}/>
        </div>
    );
}