"use server"

import { S3Client, GetObjectCommand, ListObjectsV2Command } from "@aws-sdk/client-s3"
import { getSignedUrl } from "@aws-sdk/s3-request-presigner"
import { db } from "@/lib/db/db"
import { auth } from "@/lib/auth"
import type { Podcasts } from "@/lib/db/schema"

const s3Client = new S3Client({
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_S3_ACCESS_KEY!,
    secretAccessKey: process.env.AWS_S3_SECRET_ACCESS_KEY!,
  },
})

const BUCKET_NAME = process.env.AWS_S3_BUCKET!
const PODCASTS_FOLDER = "podcasts/"

export async function getUserPodcasts() {
  const session = await auth()

  if (!session?.user?.email) {
    throw new Error("Not authenticated")
  }

  const user = await db
    .selectFrom("users")
    .select("id")
    .where("email", "=", session.user.email)
    .executeTakeFirst()

  if (!user) {
    throw new Error("User not found")
  }

  const podcasts = await db
    .selectFrom("podcasts")
    .selectAll()
    .where("user_id", "=", user.id)
    .orderBy("date_created", "desc")
    .execute()

  return podcasts
}

export async function getPodcastById(podcastId: number) {
  const session = await auth()

  if (!session?.user?.email) {
    throw new Error("Not authenticated")
  }

  const user = await db
    .selectFrom("users")
    .select("id")
    .where("email", "=", session.user.email)
    .executeTakeFirst()

  if (!user) {
    throw new Error("User not found")
  }

  const podcast = await db
    .selectFrom("podcasts")
    .selectAll()
    .where("id", "=", podcastId)
    .where("user_id", "=", user.id)
    .executeTakeFirst()

  if (!podcast) {
    throw new Error("Podcast not found")
  }

  return podcast
}

export async function getPodcastSignedUrl(s3Key: string) {
  const session = await auth()

  if (!session?.user?.email) {
    throw new Error("Not authenticated")
  }

  if (!s3Key.startsWith(PODCASTS_FOLDER)) {
    s3Key = PODCASTS_FOLDER + s3Key
  }

  const command = new GetObjectCommand({
    Bucket: BUCKET_NAME,
    Key: s3Key,
  })

  const signedUrl = await getSignedUrl(s3Client, command, {
    expiresIn: 3600
  })

  return signedUrl
}

export async function listPodcastsInS3() {
  const session = await auth()

  if (!session?.user?.email) {
    throw new Error("Not authenticated")
  }

  const command = new ListObjectsV2Command({
    Bucket: BUCKET_NAME,
    Prefix: PODCASTS_FOLDER,
  })

  const response = await s3Client.send(command)

  const files = response.Contents?.filter(
    (item) => item.Key && item.Key !== PODCASTS_FOLDER
  ).map((item) => ({
    key: item.Key!,
    size: item.Size || 0,
    lastModified: item.LastModified || new Date(),
  })) || []

  return files
}

export async function getPodcastWithSignedUrl(podcastId: number) {
  const podcast = await getPodcastById(podcastId)

  if (!podcast.s3_link) {
    throw new Error("Podcast has no S3 link")
  }

  const signedUrl = await getPodcastSignedUrl(podcast.s3_link)

  return {
    ...podcast,
    playbackUrl: signedUrl,
  }
}
