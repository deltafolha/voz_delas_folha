import axios from "axios";
import { useState, useEffect } from "react";

export default function ChartAuthorFilter(props) {
    const [authors, setAuthors] = useState(["⏱ CARREGANDO JORNALISTAS"]);

    useEffect(() => {
        async function getAuthors() {
            const authorFetchResponse = await axios.get("/api/authors");
            const authorOptions = ["TODAS"].concat(authorFetchResponse.data.result.map((author) => author.name));
            setAuthors(authorOptions);
        }
        getAuthors();
    }, []);

    const authorSelected = (event) => {
        props.setSelectedAuthor(event.target.value);
    }

    return (
        <>
            <div className="w-3/6 p-0.5 text-xs">
                <h2 className="text-xs mb-2 text-gray-700">SELECIONE UMA PESSOA AUTORA</h2>
                <div className="sticky">
                    <select id="author" name="author" onChange={authorSelected} className="block appearance-none w-full bg-white border border-gray-200 text-gray-700 text-xs py-3 px-4 pr-8 rounded leading-tight focus:outline-none hover:border-gray-400">
                        {authors.map((author, index) => <option key={index}>{author}</option>)}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /></svg>
                    </div>
                </div>
            </div>
        </>
    )
}