import axios from "axios";
import { useState, useEffect } from "react";

export default function ChartChannelFilter(props) {
    const [channels, setChannels] = useState(["⏱ CARREGANDO EDITORIAS"]);

    useEffect(() => {
        async function getChannels() {
            const channelFetchResponse = await axios.get("/api/channels");
            const channelOptions = ["TODAS"].concat(channelFetchResponse.data.result.map((channel => channel.name)));
            setChannels(channelOptions);
        }
        getChannels();
    }, []);

    const channelSelected = (event) => {
        props.setSelectedChannel(event.target.value);
    }

    return (
        <>
            <div className="w-3/6 p-0.5 text-xs">
                <h2 className="text-xs mb-2 text-gray-700">SELECIONE UMA EDITORIA</h2>
                <div className="sticky">
                    <select id="channel" name="channel" onChange={channelSelected} className="block appearance-none w-full bg-white border border-gray-200 text-gray-700 text-xs py-3 px-4 pr-8 rounded leading-tight focus:outline-none hover:border-gray-400">
                        {channels.map((channel, index) => <option key={index}>{channel}</option>)}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
                    </div>
                </div>
            </div>
        </>
    )
}