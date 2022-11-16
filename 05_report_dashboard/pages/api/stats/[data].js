import { BigQuery } from "@google-cloud/bigquery"

String.prototype.format = function () {
    var i = 0, args = arguments;
    return this.replace(/{}/g, function () {
      return typeof args[i] != 'undefined' ? args[i++] : '';
    });
};

function resolveQuery(user_query, startDate, endDate, selectedChannel, selectedAuthor) {
    const unnestAuthors = selectedAuthor === "TODAS" ? "" : ", UNNEST(authors) as writers";

    let filterByChannelAndAuthor = ""
    filterByChannelAndAuthor = filterByChannelAndAuthor.concat(selectedChannel === "TODAS" ? "" : "AND channel.name = '{}' ".format(selectedChannel));
    filterByChannelAndAuthor = filterByChannelAndAuthor.concat(selectedAuthor === "TODAS" ? "" : "AND writers.name = '{}' ".format(selectedAuthor));
    console.log(user_query.format(unnestAuthors, startDate, endDate, filterByChannelAndAuthor))
    return user_query.format(unnestAuthors, startDate, endDate, filterByChannelAndAuthor);
}

export default async function getStatsWithinTimeRange (req, res) {
    if (req.method === "GET") {
        const { data, startDate, endDate, selectedChannel, selectedAuthor } = req.query;
        const user_query = process.env["QUERY_" + data.toUpperCase()]
        
        if (user_query == undefined) {
            res.status(404);
        }
        else {
            const bigqueryClient = new BigQuery();
            const query = resolveQuery(user_query, startDate, endDate, selectedChannel, selectedAuthor);
            const [rows] = await bigqueryClient.query(query);
            res.status(200).json({
                result: rows
            });
        }
    }
    else {
        res.status(405);
    }
    res.end();
}