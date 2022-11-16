import DatePicker from "react-datepicker";

export default function ChartDateFilter (props) {
    const [ startDate, endDate ] = props.dateRange;
    return (
        <>
            <h2 className="text-xs mb-2 text-gray-700">SELECIONE UM PERÍODO DE ANÁLISE</h2>
            <div className="w-full mb-5 text-xs">
                <DatePicker className="w-full border border-gray-200 text-gray-700 text-xs py-3 px-4 pr-8 rounded leading-tight focus:outline-none hover:border-gray-400 cursor-default"
                    selectsRange={true}
                    startDate={startDate}
                    endDate={endDate}
                    dateFormat="dd/MM/yyyy"
                    onChange={(update) => {
                        props.setDateRange(update);                        
                    }}
                />
            </div>
        </>
    )
}