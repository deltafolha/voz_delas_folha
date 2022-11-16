import axios from "axios";
import React, { useEffect, useState } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

export default function ChartSpeakers (props) {
    const [ labels, setLabels ] = useState([""]);
    const [ totalFemaleSpeakers, setTotalFemaleSpeakers ] = useState(0);
    const [ totalMaleSpeakers, setTotalMaleSpeakers ] = useState(0);
    const [ totalUndefinedGenderSpeakers, setTotalUndefinedGenderSpeakers ] = useState(0);

    const data = {
        labels,
        datasets: [
            {
                label: 'Homens',
                data: [totalMaleSpeakers],
                borderColor: 'rgb(251, 192, 45)',
                backgroundColor: 'rgb(251, 192, 45, 0.8)',
            },
            {
                label: 'Mulheres',
                data: [totalFemaleSpeakers],
                borderColor: 'rgb(76, 175, 80)',
                backgroundColor: 'rgb(76, 175, 80, 0.8)',
            },
            {
                label: 'Fontes não categorizadas',
                data: [totalUndefinedGenderSpeakers],
                borderColor: 'rgb(188, 80, 144)',
                backgroundColor: 'rgb(188, 80, 144, 0.8)',
            },
        ],
      };

    const options = {
        indexAxis: 'y',
        elements: {
            bar: {
                borderWidth: 2,
            },
        },
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                stacked: true,
            },
            y: {
                stacked: true,
            }
        },
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: false,
                text: '',
            },
        },
    };

    useEffect(() => {
        async function getQuotesWithinTimeRange() {
            //IT MEANS THE USER SELECTED THE TWO DATES FROM THE DATE PICKER
            if (!props.dateRange.includes(null)) {
                const startDate = props.dateRange[0].toISOString().split("T")[0];
                const endDate = props.dateRange[1].toISOString().split("T")[0];

                const speakers = await axios.get(`/api/stats/quotes?startDate=${startDate}&endDate=${endDate}&selectedChannel=${props.selectedChannel}&selectedAuthor=${props.selectedAuthor}`);
                const result = speakers.data.result[0];
                setTotalFemaleSpeakers(result.total_female_quotes);
                setTotalMaleSpeakers(result.total_male_quotes);
                setTotalUndefinedGenderSpeakers(result.total_undefined_gender_quotes);
            }
        }
        getQuotesWithinTimeRange();
    }, [props.dateRange, props.selectedChannel, props.selectedAuthor])
       
    return <Bar options={options} data={data} height="80px"/>;
}