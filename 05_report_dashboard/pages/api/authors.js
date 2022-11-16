import { BigQuery } from "@google-cloud/bigquery";

export default async function getAuthors(req, res) {
    if (req.method === "GET") {
        const bigqueryClient = new BigQuery();
        const [rows] = await bigqueryClient.query(process.env.QUERY_AUTHORS);
        res.status(200).json({
            result: rows
        });
    }
    else {
        res.status(405);
    }
    res.end();
}