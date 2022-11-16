import Navbar from "../components/Navbar";
import React, { useState } from "react";
import { useSession } from "next-auth/react";
import { isMobile } from 'react-device-detect';
import ChartContainer from "../components/ChartContainer";
import ChartTexts from "../components/ChartTexts";
import ChartPercentage from "../components/ChartPercentage";
import ChartSpeakers from "../components/ChartSpeakers";
import ChartQuotes from "../components/ChartQuotes";
import ChartSpace from "../components/ChartSpace";
import FilterContainer from "../components/FilterContainer";
import "react-datepicker/dist/react-datepicker.css";

function calculateStartAndEndDate(someDaysAgo) {
    var start_date = new Date();
    var end_date = new Date();

    start_date.setDate(start_date.getDate() - someDaysAgo);
    start_date.setHours(0, 0, 0, 0);

    end_date.setDate(end_date.getDate() - 1);
    end_date.setHours(0, 0, 0, 0);

    return [start_date, end_date]
}

export default function Dashboard() {
    const { status, data } = useSession();
    const [dateRange, setDateRange] = useState(calculateStartAndEndDate(parseInt(process.env.NEXT_PUBLIC_QUERY_DEFAULT_TIME_INTERVAL)));
    const [selectedChannel, setSelectedChannel] = useState("TODAS");
    const [selectedAuthor, setSelectedAuthor] = useState("TODAS")

    return (
        <>
            <Navbar isMobile={isMobile} user={data?.user.name} />
            <section className="flex flex-wrap min-h-screen py-20 bg-gray-100">
                <FilterContainer dateRange={dateRange} setDateRange={setDateRange} selectedChannel={selectedChannel} setSelectedChannel={setSelectedChannel} selectedAuthor={selectedAuthor} setSelectedAuthor={setSelectedAuthor}/>
                <ChartContainer child={<ChartTexts dateRange={dateRange} selectedChannel={selectedChannel} selectedAuthor={selectedAuthor}/>} title="TOTAL DE TEXTOS" />
                <ChartContainer child={<ChartPercentage dateRange={dateRange} selectedChannel={selectedChannel} selectedAuthor={selectedAuthor}/>} title="MULHERES CITADAS (%)" />
                <ChartContainer child={<ChartSpeakers dateRange={dateRange} selectedChannel={selectedChannel} selectedAuthor={selectedAuthor}/>} title="PESSOAS CITADAS, POR GÊNERO" />
                <ChartContainer child={<ChartQuotes dateRange={dateRange} selectedChannel={selectedChannel} selectedAuthor={selectedAuthor}/>} title="CITAÇÕES, POR GÊNERO" />
                <ChartContainer child={<ChartSpace dateRange={dateRange} selectedChannel={selectedChannel} selectedAuthor={selectedAuthor}/>} title="ESPAÇO DADO EM CARACTERES" />
            </section>
        </>
    )
}