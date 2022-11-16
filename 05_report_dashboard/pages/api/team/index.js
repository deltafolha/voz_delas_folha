import { getToken } from "next-auth/jwt";
const Knex = require('knex');

export default async function team (req, res) {
    const token = await getToken({ req });
    if (token) {
      if (req.method === "GET") {
        const pool = await createUnixSocketPool();
        const teamResponse = await pool.select().from("team");
        pool.destroy();
        res.status(200).json({
            team : teamResponse
        });
      } 
      else {
        res.status(405);
      }
    }
    else {
      res.status(401);
    }
    res.end();
}

const createUnixSocketPool = async config => {
    return Knex({
      client: 'pg',
      connection: {
        user: process.env.DB_USER,
        password: process.env.DB_PASS,
        database: process.env.DB_NAME,
        host: process.env.DB_PUBLIC_IP,
      },
      ...config,
    });
  };