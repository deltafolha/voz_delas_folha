import axios from "axios";
import moment from "moment";
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

export default function ChartPercentage(props) {
    const [labels, setLabels] = useState([]);
    const [femaleSpeakersPercentage, setFemaleSpeakersPercentage] = useState([]);

    const data = {
        labels,
        datasets: [
            {
                label: '% de mulheres citadas entre todas as fontes identificadas nos textos',
                data: femaleSpeakersPercentage,
                backgroundColor: 'rgba(53, 162, 235, 0.5)',
            }
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            title: {
                display: false,
                text: "",
            },
            legend: {
                position: 'top',
            },
        },
        scales: {
            y: {
                min: 0,
                max: 100
            }
        }
    };

    useEffect(() => {
        async function getFemaleSpeakersPercentageWithinTimeRange() {
            //IT MEANS THE USER SELECTED THE TWO DATES FROM THE DATE PICKER
            if (!props.dateRange.includes(null)) {
                const startDate = props.dateRange[0].toISOString().split("T")[0];
                const endDate = props.dateRange[1].toISOString().split("T")[0];

                const total_texts = await axios.get(`/api/stats/percentage?startDate=${startDate}&endDate=${endDate}&selectedChannel=${props.selectedChannel}&selectedAuthor=${props.selectedAuthor}`);

                const dataAmount = total_texts.data.result.length;
                const expectedDataAmount = moment(endDate, "YYYY-MM-DD").diff(moment(startDate, "YYYY-MM-DD"), 'days') + 1;

                setLabels([]);
                setFemaleSpeakersPercentage([]);

                if (dataAmount == expectedDataAmount) {
                    total_texts.data.result.forEach(row => {
                        setLabels(prevState => [...prevState, row.date.value]);
                        setFemaleSpeakersPercentage(prevState => [...prevState, row.percentage]);
                    });
                }
                else {
                    let momentStartDate = moment(startDate);
                    let tempLabels = [];
                    let tempFemaleSpeakersPercentage = [];

                    while (momentStartDate.isSameOrBefore(moment(endDate))) {
                        tempLabels.push(momentStartDate.format("YYYY-MM-DD"));
                        tempFemaleSpeakersPercentage.push(0);
                        momentStartDate.add(1, "days");
                    }

                    total_texts.data.result.forEach(row => {
                        const index = tempLabels.indexOf(row.date.value);
                        tempFemaleSpeakersPercentage[index] = row.percentage;
                    });

                    setLabels(tempLabels);
                    setFemaleSpeakersPercentage(tempFemaleSpeakersPercentage);
                }

            }
        }
        getFemaleSpeakersPercentageWithinTimeRange();
    }, [props.dateRange, props.selectedChannel, props.selectedAuthor])

    return <Bar options={options} data={data} />;
}