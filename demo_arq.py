from arq import CanalSimule, RecepteurARQ, EmetteurARQ
def main():
    r=RecepteurARQ(); e=EmetteurARQ(CanalSimule(["ok","perte_i","ok"]),r)
    recu=e.transferer(b"A"*49)
    print("Scénario perte I :", recu, e.stats)
    r=RecepteurARQ(); e=EmetteurARQ(CanalSimule(["perte_ack","ok"]),r)
    print("Scénario perte ACK/doublon :", e.transferer(b"G8"), e.stats)
if __name__ == "__main__": main()
