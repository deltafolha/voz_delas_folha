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

export default function ChartTexts(props) {
    const [labels, setLabels] = useState([]);
    const [textsWithFemaleSpeakers, setTextsWithFemaleSpeakers] = useState([]);
    const [textsWithoutFemaleSpeakers, setTextsWithoutFemaleSpeakers] = useState([]);
    const [textsWithoutSpeakers, setTextsWithoutSpeakers] = useState([]);
    const [textsWithError, setTextsWithError] = useState([]);

    const data = {
        labels,
        datasets: [
            {
                label: 'Textos com pelo menos uma mulher citada',
                data: textsWithFemaleSpeakers,
                backgroundColor: '#bc5090',
            },
            {
                label: 'Textos com citações, sem mulheres',
                data: textsWithoutFemaleSpeakers,
                backgroundColor: 'rgb(255, 166, 0)',
            },
            {
                label: 'Textos sem citações',
                data: textsWithoutSpeakers,
                backgroundColor: 'rgb(75, 192, 192)',
            },
            {
                label: 'Textos com erros',
                data: textsWithError,
                backgroundColor: 'rgb(255, 99, 132)',
            },
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
            }
        },
        scales: {
            x: {
                stacked: true,
            },
            y: {
                stacked: true,
                ticks: {
                    precision: 0
                }
            },
        },
    };

    useEffect(() => {
        async function getStatsFromTextsWithinTimeRange() {
            //IT MEANS THE USER SELECTED THE TWO DATES FROM THE DATE PICKER
            if (!props.dateRange.includes(null)) {
                const startDate = props.dateRange[0].toISOString().split("T")[0];
                const endDate = props.dateRange[1].toISOString().split("T")[0];

                const total_texts = await axios.get(`/api/stats/texts?startDate=${startDate}&endDate=${endDate}&selectedChannel=${props.selectedChannel}&selectedAuthor=${props.selectedAuthor}`);

                const dataAmount = total_texts.data.result.length;
                const expectedDataAmount = moment(endDate, "YYYY-MM-DD").diff(moment(startDate, "YYYY-MM-DD"), 'days') + 1;

                setLabels([]);
                setTextsWithFemaleSpeakers([]);
                setTextsWithoutFemaleSpeakers([]);
                setTextsWithoutSpeakers([]);
                setTextsWithError([]);

                if (dataAmount == expectedDataAmount) {
                    total_texts.data.result.forEach(row => {
                        setLabels(prevState => [...prevState, row.date.value]);
                        setTextsWithFemaleSpeakers(prevState => [...prevState, row.texts_with_female_speakers]);
                        setTextsWithoutFemaleSpeakers(prevState => [...prevState, row.texts_without_female_speakers]);
                        setTextsWithoutSpeakers(prevState => [...prevState, row.texts_without_speakers]);
                        setTextsWithError(prevState => [...prevState, row.text_with_error]);
                    });
                }
                else {
                    let momentStartDate = moment(startDate);
                    let tempLabels = [];
                    let tempTextsWithFemaleSpeakers = [];
                    let tempTextsWithoutFemaleSpeakers = [];
                    let tempTextsWithoutSpeakers = [];
                    let tempTextsWithError = [];

                    while (momentStartDate.isSameOrBefore(moment(endDate))) {
                        tempLabels.push(momentStartDate.format("YYYY-MM-DD"));
                        tempTextsWithFemaleSpeakers.push(0);
                        tempTextsWithoutFemaleSpeakers.push(0);
                        tempTextsWithoutSpeakers.push(0);
                        tempTextsWithError.push(0);
                        momentStartDate.add(1, "days");
                    }

                    total_texts.data.result.forEach(row => {
                        const index = tempLabels.indexOf(row.date.value);
                        tempTextsWithFemaleSpeakers[index] = row.texts_with_female_speakers;
                        tempTextsWithoutFemaleSpeakers[index] = row.texts_without_female_speakers;
                        tempTextsWithoutSpeakers[index] = row.texts_without_speakers;
                        tempTextsWithError[index] = row.text_with_error;
                    });

                    setLabels(tempLabels);
                    setTextsWithFemaleSpeakers(tempTextsWithFemaleSpeakers);
                    setTextsWithoutFemaleSpeakers(tempTextsWithoutFemaleSpeakers);
                    setTextsWithoutSpeakers(tempTextsWithoutSpeakers);
                    setTextsWithError(tempTextsWithError);
                }

            }
        }
        getStatsFromTextsWithinTimeRange();
    }, [props.dateRange, props.selectedChannel, props.selectedAuthor])

    return <Bar options={options} data={data} />;
}