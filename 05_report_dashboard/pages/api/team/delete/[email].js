import { getToken } from "next-auth/jwt";
const Knex = require('knex');

export default async function deleteTeamMember (req, res) {
    const token = await getToken({ req });
    if (token) {
      if (req.method === "DELETE") {
        const email = req.query.email;
        const pool = await createUnixSocketPool();
        const deleteTeamMemberResponse = await pool.from("team").where("email", email).delete();
        pool.destroy();
        res.status(200).json({
            result : deleteTeamMemberResponse
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